import requests
import concurrent.futures
import re
import json
import logging
import os
import pytz
import random

from connections.connection import Connection
from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import MangaMonsterBucketEnum, ErrorCategoryEnum, MangaSourceEnum
from configs.config import MAX_THREADS, S3_ROOT_DIRECTORY,INSERT_QUEUE
from utils.crawler_util import get_soup, format_chapter_number, format_leading_chapter, hashidx, image_s3_upload, format_leading_img_count, format_leading_part
from models.entities import Manga, MangaChapters, MangaChapterResources
from datetime import datetime
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

header = {
    'User-Agent':'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'
}

class MangaseeCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Mangasee crawler created')
        return MangaseeCrawler()

class MangaseeCrawler(Crawler):

    def crawl(self):
        logging.info('Crawling all mangas from Mangasee...')
        # Connect MongoDB
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_collection = mongo_db['tx_mangas']
        
        list_manga_url = 'https://mangasee123.com/_search.php'
        list_manga_request = requests.post(list_manga_url).json()
        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            # Submit each manga for processing to the executor
            for manga in list_manga_request:
                manga_slug = manga['i']
                manga_url = f'https://mangasee123.com/manga/{manga_slug}'
                future = executor.submit(self.extract_manga_info, manga_url, manga_slug, mongo_collection)
                futures.append(future)

            # Wait for all tasks to complete and get the results
        for future in futures:
            future.result()
        
            
    def update_chapter(self):
        logging.info('Updating new chapters...')
        # Connect DB
        db = Connection().mysql_connect()
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        tx_manga_errors = mongo_db['tx_manga_errors']
        s3 = Connection().s3_connect()
        insert_queue = Connection().redis_connect(db=2, queue_name=INSERT_QUEUE)
        
        manga_url = 'https://mangasee123.com/'
        soup = get_soup(manga_url, header=header)
        script = soup.findAll('script')[-1].text
        regex_hot_update = r'vm.HotUpdateJSON\s=\s.{0,};'
        regex_latest_json = r'vm.LatestJSON\s=\s.{0,};'
        hot_update_match = re.search(regex_hot_update, script)
        latest_json_match = re.search(regex_latest_json, script)
        list_latest_json = []
        list_hot_update = []
        if hot_update_match:
            hot_update_str = hot_update_match.group().replace('vm.HotUpdateJSON = ', '').replace(';', '')
            list_hot_update = json.loads(hot_update_str)
        if latest_json_match:
            latest_json_str = latest_json_match.group().replace('vm.LatestJSON = ', '').replace(';', '')
            list_latest_json = json.loads(latest_json_str)
        list_update_manga = list_hot_update + list_latest_json
        for item in list_update_manga:
            chapter_encoded = self.chapter_encode(item['Chapter'])
            # Get manga from DB
            db_manga = db.query(Manga).where(Manga.slug == item['IndexName'].lower()).first()
            if db_manga is not None:
                # Check if manga has chapter
                index_string = item['Chapter'][0:1]
                if index_string == '1':
                    season = 0
                else:
                    season = int(index_string)
                db_manga_chapter = db.query(MangaChapters).where(MangaChapters.manga_id == db_manga.id).where(MangaChapters.ordinal == float(format_chapter_number(item['Chapter']))).where(MangaChapters.season == season).where(MangaChapters.status == 1).first()
                if db_manga_chapter is None:
                    chapter_url = 'https://mangasee123.com/read-online/{}{}-page-1.html'.format(item['IndexName'], chapter_encoded)
                    logging.info(chapter_url)
                    chapter_source, chapter_info, index_name = self.get_chapter_info(chapter_url)
                    if chapter_info['Directory'] and chapter_info['Directory'] != '':
                        directory = chapter_info['Directory']
                        directory_slug = '-' + directory
                        directory_name = directory + ' - '
                    else:
                        directory_slug = ''
                        directory_name = ''
                    manga_id = db_manga.id
                    formatted_chapter_number = format_leading_chapter(format_chapter_number(item['Chapter']))
                    resource_status = 'STORAGE'
                    manga_bucket = tx_manga_bucket_mapping.find_one({'url':item['IndexName']})['bucket']
                    
                    # Download image to S3
                    for i in range(1, int(chapter_info['Page']) + 1):
                        directory = None
                        image_url = None
                        if chapter_info['Directory'] and chapter_info['Directory'] != '':
                            directory = chapter_info['Directory']

                        image_url = self.get_image_url(chapter_source=chapter_source, slug=item['IndexName'], directory=directory,
                                                    formatted_chapter_number=formatted_chapter_number, formatted_img_count=format_leading_img_count(i))
                        logging.info(image_url)
                        try:
                            image_s3_upload(s3, root_directory=S3_ROOT_DIRECTORY, image_url=image_url, manga_no=format_chapter_number(
                                chapter_info['Chapter']), formatted_img_count=format_leading_img_count(i), slug=item['IndexName'], season=season, bucket=manga_bucket)
                        except Exception as ex:
                            resource_status = 'ORIGINAL'
                            error_dict = {
                                'error_type':ErrorCategoryEnum.S3_UPLOAD.value,
                                'chapter_url':chapter_url,
                                'bucket':manga_bucket,
                                'slug':item['IndexName']
                            }
                            tx_manga_errors.insert_one(error_dict)
                            break
                    chapter_dict = {
                        "name": '{}Chapter {}'.format(directory_name,
                                                        format_chapter_number(item['Chapter'])),
                        "slug": item['IndexName'].lower() + directory_slug.lower() + '-chapter-' + format_chapter_number(item['Chapter']).replace('.','-'),
                        "original": chapter_url,
                        "published": item['Date'],
                        "manga_id": manga_id,
                        "ordinal": float(format_chapter_number(item['Chapter'])),
                        'resource_status':resource_status,
                        "season": season,
                        'status': 1,
                        'total_view': 0,
                        'created_by': 0,
                        'updated_by': 0,
                        'deleted_by': 0,
                        'created_at': item['Date'],
                        'updated_at': item['Date'],
                    }
                    # Insert to database
                    manga_chapter_obj = MangaChapters(**chapter_dict)
                    insert_resources = self.insert_db(db=db, chapter_obj=manga_chapter_obj, row_id=manga_id, pages=int(chapter_info['Page']))
                    if insert_resources:
                        manga_ordinal = format_leading_chapter(int(chapter_dict['ordinal']))
                        season_path = format_leading_part(int(season))
                        manga_part = format_leading_part(int(float(chapter_dict['ordinal']) % 1 * 10))
                        manga_slug = item['IndexName']
                        thumb_format = f'{manga_slug.lower()}/{season_path}/{manga_ordinal}/{manga_part}'
                        if chapter_info['Directory']:
                            original_format = f'https://{chapter_source}/manga/{manga_slug}/' + chapter_info['Directory'] + formatted_chapter_number
                        else:
                            original_format = f'https://{chapter_source}/manga/{manga_slug}/' + formatted_chapter_number

                        insert_queue.enqueue(insert_resources, args=(manga_id, chapter_dict['slug'], thumb_format, original_format,
                                                                            int(chapter_info['Page']),chapter_json['Date'], manga_bucket))
                else:
                    logging.info('New chapter %s for manga %s existed' % (item['Chapter'], item['IndexName']))
                    
    def update_manga(self):
        logging.info('Updating new mangas...')
        # Connect DB
        db = Connection().mysql_connect()
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        tx_mangas = mongo_db['tx_mangas']
        
        manga_url = 'https://mangasee123.com/'
        soup = get_soup(manga_url, header=header)
        script = soup.findAll('script')[-1].text
        regex = r'vm.NewSeriesJSON\s=\s.{0,};'
        list_new_mangas_match = re.search(regex, script)
        if list_new_mangas_match: 
            new_mangas_str = list_new_mangas_match.group().replace('vm.NewSeriesJSON = ', '').replace(';', '')
            list_mangas = new_mangas_str.strip('][').split('},')
        for manga in list_mangas:
            manga_json = self.string_to_json(manga)
            # Check if manga existed
            existed_manga = db.query(Manga).where(Manga.slug == manga_json['IndexName'].lower()).first()
            if existed_manga is None:
                manga_url = 'https://mangasee123.com/manga/{}'.format(manga_json['IndexName'])
                self.extract_manga_info(manga_url=manga_url, manga_slug=manga_json['IndexName'],mongo_collection=tx_mangas)
                # manga_thumb = manga_soup.find('meta', {'property': 'og:image'})['content']
                # img = Image.open(BytesIO(requests.get(manga_thumb).content))
                # today = datetime.now()
                # today_str = '{}/{}/{}'.format(str(today.year),
                #                                 str(today.month), str(today.day))
                # thumb_path = 'images/manga/{}/{}.jpg'.format(
                #     today_str, manga_json['IndexName'].lower())
                # thumb_save_path = f'/www-data/mangamonster.com/storage/app/public/{thumb_path}'
                # logging.info(thumb_save_path)
                # os.makedirs(os.path.dirname(thumb_save_path), exist_ok=True)
                # img.convert('RGB').save(thumb_save_path)
                # manga_dict = {
                #     'name': manga_name,
                #     'slug': manga_json['IndexName'].lower(),
                #     'original': manga_url,
                #     'thumb': thumb_path,
                #     'type': 1,
                #     'status': 1,
                #     'total_view': 0,
                #     'created_by': 0,
                #     'updated_by': 0,
                #     'deleted_by': 0,
                #     'created_at': datetime.now(tz=pytz.timezone('America/Chicago')),
                #     'updated_at': datetime.now(tz=pytz.timezone('America/Chicago')),
                #     'slug_original': manga_json['IndexName']
                # }
                # manga_dict.update(manga_raw_info_dict)
                # logging.info('Manga dict %s' % manga_dict)

                # if 'alternate_name' in manga_dict.keys():
                #     del manga_dict['alternate_name']
                # type_text = ''
                # if manga_dict['type'] == 1:
                #     type_text = 'Manga'
                # elif manga_dict['type'] == 2:
                #     type_text = 'Manhua'
                # manga_dict['search_text'] = manga_dict.get('name', '') + manga_dict.get(
                #     'description', '') + manga_dict.get('author', '') + manga_dict.get('genre', '')
                # manga_dict['search_field'] = manga_dict.get(
                #     'name', '') + type_text + manga_dict.get('author', '') + manga_dict.get('genre', '')
                
                # manga_obj = Manga(**manga_dict)
                # try:
                #     db.add(manga_obj)
                #     db.commit()
                #     logging.info('NEW MANGA INSERTED')
                # except Exception as ex:
                #     db.rollback()
                
                # query_new_manga = db.query(Manga).where(Manga.slug == manga_dict['slug'])
                # new_manga = query_new_manga.first()
                # if new_manga is not None:
                #     idx = hashidx(new_manga.id)
                #     update_value = {
                #         'idx': idx,
                #         'local_url':'https://mangamonster.net/' + manga_json['IndexName'].lower() + '-m' + idx
                #     }
                #     query_new_manga.update(update_value)
                #     db.commit()
                
                list_buckets = [item.value for item in MangaMonsterBucketEnum]
                selected_bucket = random.choice(list_buckets)
                bucket_mapping_data = {
                    'url':manga_json['IndexName'],
                    'bucket':selected_bucket
                }
                tx_manga_bucket_mapping.insert_one(bucket_mapping_data)
                
                # db.close()
            else:
                existed_manga_bucket_mapping = tx_manga_bucket_mapping.find_one({'url':manga_json['IndexName']})
                logging.info('Manga %s existed in bucket %s with ID %s' % (manga_json['IndexName'], existed_manga_bucket_mapping['bucket'], existed_manga.id))

    def process_detail(self, manga_soup):
        list_group_flush = manga_soup.find('ul', {'class': 'list-group-flush'})
        info_group = list_group_flush.find_all('li', {'class': 'list-group-item'})[2]
        manga_raw_info_dict = {}
        list_info = str(info_group).split("\n\n")
        for info in list_info[:-1]:
            new_info = info.strip(
                """ <li class="list-group-item {{vm.ShowInfoMobile ? '' : 'd-none d-md-block' }}"> """)
            new_info_soup = BeautifulSoup(new_info, 'html.parser')
            if new_info_soup.find('span') is not None:
                field = new_info_soup.find('span').text.replace('\n', '').replace('(s)', '').replace(':',
                                                                                                        '').lower()
                if len(new_info_soup.find_all('a')) > 0:
                    value = ','.join([x.text.strip('</')
                                        for x in new_info_soup.find_all('a')])
                else:
                    value = ' '.join(new_info_soup.find(
                        'div', {'class': 'top-5'}).text.strip('</').split())
                if field != 'status':
                    if len(field.split(' ')) > 1:
                        field = '_'.join(field.split(' '))
                    if field == 'released':
                        field = 'published'
                    if field == 'description':
                        value = " ".join(value.split()) + \
                            ' (Source: Mangamonster.net)'
                    manga_raw_info_dict[field] = value
        return manga_raw_info_dict
        
    def extract_manga_info(self,manga_url,manga_slug, mongo_collection):
        try:
            logging.info(manga_url)
            manga_soup = get_soup(manga_url, header=header)
            manga_name = manga_soup.find('meta', {'property': 'og:title'})['content'].split('|')[0].strip()
            manga_thumb = manga_soup.find('meta', {'property': 'og:image'})['content']
            regex = r'vm.Chapters\s=\s.{0,};'
            script = manga_soup.findAll('script')[-1].text
            list_chapters_str_regex = re.search(regex, script)
            if list_chapters_str_regex is None:
                print(f'{manga_url} error list_chapters_str_regex')
                return None
            list_chapters_str = list_chapters_str_regex.group()
            a = list_chapters_str.replace('vm.Chapters = ', '').replace(';', '')
            list_chapters = a.strip('][').split('},')
            manga_count_chapters = len(list_chapters)
            list_chapters_info = []
            if '' not in list_chapters:
                for chapter in list_chapters:
                    chapter_json = self.string_to_json(chapter)   
                    chapter_encoded = self.chapter_encode(chapter_json['Chapter'])
                    chapter_url = 'https://mangasee123.com/read-online/{}{}.html'.format(manga_slug, chapter_encoded)
                    chapter_source, chapter_info, index_name = self.get_chapter_info(chapter_url)
                    chapter_info_dict = {
                        'chapter_info': chapter_info, 
                        'chapter_source': chapter_source
                    }
                    list_chapters_info.append(chapter_info_dict)
            final_dict = {
                'name':manga_name,
                'original':manga_url,
                'slug': manga_slug,
                'thumb':manga_thumb,
                'count_chapters': manga_count_chapters, 
                'chapters': list_chapters_info, 
                'source_site':MangaSourceEnum.MANGASEE.value}
            manga_raw_info_dict = self.process_detail(manga_soup)
            final_dict.update(manga_raw_info_dict)
            
            # Insert or Update 
            filter_criteria = {"slug": final_dict["slug"]}
            mongo_collection.update_one(filter_criteria, {"$set": final_dict}, upsert=True)
            # mongo_collection.insert_one(final_dict)
            logging.info('%s INSERTED TO DB' % manga_url)
        except Exception as ex:
            logging.error(str(ex))
            
            
    def push_to_db(self):
        return super().push_to_db()
        
    def string_to_json(self, chapter_str):
        if not chapter_str.endswith('}'):
            chapter_str += '}'
        return json.loads(chapter_str)


    def chapter_encode(self, chapter_string):
        index = ''
        index_string = chapter_string[0:1]
        if index_string != '1':
            index = '-index-{}'.format(index_string)
        chapter = int(chapter_string[1:-1])
        odd = ''
        odd_string = chapter_string[len(chapter_string) - 1]
        if odd_string != '0':
            odd = '.{}'.format(odd_string)
        return '-chapter-{}{}{}'.format(chapter, odd, index)

    def get_chapter_info(self, chapter_url):
        chapter_source = None
        chapter_info = None
        index_name = None
        chapter_script = self.extract_script(chapter_url)
        chapter_regex = r'vm.CurChapter\s=\s.{0,};'
        chapter_source_regex = r'vm.CurPathName\s=\s.{0,};'
        index_name_regex = r'vm.IndexName\s=\s.{0,};'
        source_match = re.search(chapter_source_regex, chapter_script)
        if source_match:
            chapter_source_str = source_match.group()
            chapter_source = chapter_source_str.replace(
                'vm.CurPathName = ', '').replace(';', '').replace('"', '')
        info_match = re.search(chapter_regex, chapter_script)
        if info_match:
            chapter_str = info_match.group()
            chapter_info = json.loads(chapter_str.replace(
                'vm.CurChapter = ', '').replace(';', ''))
        index_match = re.search(index_name_regex, chapter_script)
        if index_match:
            index_name_str = index_match.group()
            index_name = index_name_str.replace(
                'vm.IndexName = ', '').replace(';', '').replace('"', '')
        return chapter_source, chapter_info, index_name

    def extract_script(self, url):
        soup = get_soup(url,header=header)
        return soup.find_all('script')[-1].text
    
    def get_image_url(self, chapter_source, slug, directory, formatted_chapter_number, formatted_img_count):
        if directory is not None:
            return 'https://{}/manga/{}/{}/{}-{}.png'.format(chapter_source, slug, directory, formatted_chapter_number, formatted_img_count)
        else:
            return 'https://{}/manga/{}/{}-{}.png'.format(chapter_source, slug, formatted_chapter_number, formatted_img_count)
        
    def insert_db(self,db, chapter_obj, row_id, pages):

        chapter_query = db.query(MangaChapters).filter(MangaChapters.manga_id == row_id,
                                                    MangaChapters.slug == chapter_obj.slug, MangaChapters.name == chapter_obj.name)

        chapter_count = chapter_query.count()
        if chapter_count == 0:
            try:
                db.add(chapter_obj)
                db.commit()
            except Exception as ex:
                db.rollback()
        else:
            logging.info('CHAPTER EXISTS')

        # Check if chapter has resources
        db_chapter_obj = chapter_query.first()
        resource_count = db.query(MangaChapterResources).filter(MangaChapterResources.manga_chapter_id == db_chapter_obj.id).count()
        if resource_count == pages:
            return False
        return True
        