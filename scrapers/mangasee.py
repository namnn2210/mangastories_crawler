from hmac import new
import requests
import concurrent.futures
import re
import json
import logging
import random

from connections.connection import Connection
from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import MangaMonsterBucketEnum, ErrorCategoryEnum, MangaSourceEnum
from configs.config import MAX_THREADS, S3_ROOT_DIRECTORY, INSERT_QUEUE
from utils.crawler_util import get_soup, format_chapter_number, format_leading_chapter, format_leading_img_count, format_leading_part, chapter_builder, process_chapter_ordinal, new_process_push_to_db, process_insert_bucket_mapping
# from models.entities import Manga, MangaChapters, MangaChapterResources
from bs4 import BeautifulSoup
from datetime import datetime


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'
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

        # list_manga_url = 'https://mangasee123.com/_search.php'
        # list_manga_request = requests.post(list_manga_url).json()
        
        list_manga_url = 'https://mangasee123.com/search/'
        soup = get_soup(list_manga_url, header=header)
        script = soup.findAll('script')[-1].text
        directory_regex = r'vm.Directory\s=\s.{0,};'
        directory_match = re.search(directory_regex, script)
        if directory_match:
            directory_json_str = directory_match.group().replace('vm.Directory = ', '').replace(';', '')
            list_mangas = json.loads(directory_json_str)
        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            # Submit each manga for processing to the executor
            for manga in list_mangas:
                future = executor.submit(
                    self.get_manga_info, manga, mongo_collection)
                futures.append(future)

        #     # Wait for all tasks to complete and get the results
        for future in futures:
            future.result()
            break
        
        # for manga in list_mangas:
        #     manga_slug = manga['i']
        #     manga_ss = manga['ss']
        #     manga_url = f'https://mangasee123.com/manga/{manga_slug}'
        #     self.get_manga_info(manga_url, manga_slug,manga_ss, mongo_collection)
        #     break
    def update_chapter(self):
        logging.info('Updating new chapters...')
        # Connect DB
        # db = Connection().mysql_connect()
        # mongo_client = Connection().mongo_connect()
        # mongo_db = mongo_client['mangamonster']
        # tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        # tx_manga_errors = mongo_db['tx_manga_errors']

        # manga_url = 'https://mangasee123.com/'
        # soup = get_soup(manga_url, header=header)
        # script = soup.findAll('script')[-1].text
        # regex_hot_update = r'vm.HotUpdateJSON\s=\s.{0,};'
        # regex_latest_json = r'vm.LatestJSON\s=\s.{0,};'
        # hot_update_match = re.search(regex_hot_update, script)
        # latest_json_match = re.search(regex_latest_json, script)
        # list_latest_json = []
        # list_hot_update = []
        # if hot_update_match:
        #     hot_update_str = hot_update_match.group().replace(
        #         'vm.HotUpdateJSON = ', '').replace(';', '')
        #     list_hot_update = json.loads(hot_update_str)
        # if latest_json_match:
        #     latest_json_str = latest_json_match.group().replace(
        #         'vm.LatestJSON = ', '').replace(';', '')
        #     list_latest_json = json.loads(latest_json_str)
        # list_update_manga = list_hot_update + list_latest_json
        # for item in list_update_manga:
        #     chapter_encoded = self.chapter_encode(item['Chapter'])
        #     # Get manga from DB
        #     db_manga = db.query(Manga).where(
        #         Manga.slug == item['IndexName'].lower()).first()
        #     if db_manga is not None:
        #         # Check if manga has chapter
        #         index_string = item['Chapter'][0:1]
        #         if index_string == '1':
        #             season = 0
        #         else:
        #             season = int(index_string)
        #         db_manga_chapter = db.query(MangaChapters).where(MangaChapters.manga_id == db_manga.id).where(MangaChapters.ordinal == float(
        #             format_chapter_number(item['Chapter']))).where(MangaChapters.season == season).where(MangaChapters.status == 1).first()
        #         if db_manga_chapter is None:
        #             chapter_url = 'https://mangasee123.com/read-online/{}{}-page-1.html'.format(
        #                 item['IndexName'], chapter_encoded)
        #             logging.info(chapter_url)
        #             chapter_source, chapter_info, index_name = self.get_chapter_info(
        #                 chapter_url)
        #             manga_bucket = tx_manga_bucket_mapping.find_one(
        #                 {'url': item['IndexName']})['bucket']
        #             chapter_info_dict = self.extract_chapter_info(
        #                 chapter_source, chapter_info, chapter_url)
        #             chapter_dict = chapter_builder(chapter_info_dict, db_manga.id)
        #             processed_chapter_dict = {'chapter_dict': chapter_dict, 'pages': len(chapter_info_dict['image_urls']), 'image_urls': chapter_info_dict['image_urls']}
        #             new_push_chapter_to_db(db, processed_chapter_dict, manga_bucket, db_manga.id,True, tx_manga_errors)
        #         else:
        #             logging.info('New chapter %s for manga %s existed' %
        #                          (item['Chapter'], item['IndexName']))

    def update_manga(self):
        logging.info('Updating new mangas...')
        # Connect DB
        # db = Connection().mysql_connect()
        # mongo_client = Connection().mongo_connect()
        # mongo_db = mongo_client['mangamonster']
        # tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        # tx_mangas = mongo_db['tx_mangas']
        # tx_manga_errors = mongo_db['tx_manga_errors']

        # manga_url = 'https://mangasee123.com/'
        # soup = get_soup(manga_url, header=header)
        # script = soup.findAll('script')[-1].text
        # regex = r'vm.NewSeriesJSON\s=\s.{0,};'
        # list_new_mangas_match = re.search(regex, script)
        # if list_new_mangas_match:
        #     new_mangas_str = list_new_mangas_match.group().replace(
        #         'vm.NewSeriesJSON = ', '').replace(';', '')
        #     list_mangas = new_mangas_str.strip('][').split('},')
        # for manga in list_mangas:
        #     manga_json = self.string_to_json(manga)
        #     # Check if manga existed
        #     existed_manga = db.query(Manga).where(
        #         Manga.slug == manga_json['IndexName'].lower()).where(Manga.status == 1).first()
        #     if existed_manga is None:
        #         manga_url = 'https://mangasee123.com/manga/{}'.format(
        #             manga_json['IndexName'])
        #         self.get_manga_info(
        #             manga_url=manga_url, manga_slug=manga_json['IndexName'], mongo_collection=tx_mangas, error=tx_manga_errors)
                
        #         selected_bucket = process_insert_bucket_mapping(manga_json['IndexName'], tx_manga_bucket_mapping)

        #     else:
        #         existed_manga_bucket_mapping = tx_manga_bucket_mapping.find_one(
        #             {'original_id': manga_json['IndexName']})
        #         logging.info('Manga %s existed in bucket %s with ID %s' % (
        #             manga_json['IndexName'], existed_manga_bucket_mapping['bucket'], existed_manga.id))

    def extract_manga_info(self,manga, manga_soup):
        list_group_flush = manga_soup.find('ul', {'class': 'list-group-flush'})
        info_group = list_group_flush.find_all(
            'li', {'class': 'list-group-item'})[2]
        manga_raw_info_dict = {}
        manga_raw_info_dict['alternative_name'] = ','.join(manga['al'])
        manga_raw_info_dict['author'] = ','.join(manga['a'])
        manga_raw_info_dict['genre'] = ','.join(manga['g'])
        manga_raw_info_dict['published'] = manga['y']
        list_info = str(info_group).split("\n\n")
        for info in list_info[:-1]:
            new_info = info.strip(
                """ <li class="list-group-item {{vm.ShowInfoMobile ? '' : 'd-none d-md-block' }}"> """)
            new_info_soup = BeautifulSoup(new_info, 'html.parser')
            if new_info_soup.find('span') is not None:
                field = new_info_soup.find('span').text.replace('\n', '').replace('(s)', '').replace(':','').lower()
                if len(new_info_soup.find_all('a')) > 0:
                    value = ','.join([x.text.strip('</')
                                      for x in new_info_soup.find_all('a')])
                else:
                    value = ' '.join(new_info_soup.find(
                        'div', {'class': 'top-5'}).text.strip('</').split())
                if field != 'status':
                    if field == 'description':
                        value = " ".join(value.split()) + \
                            ' (Source: Mangamonster.net)'
                        manga_raw_info_dict[field] = value
        return manga_raw_info_dict

    def get_manga_info(self, manga, mongo_collection):
        try:
            mongo_client = Connection().mongo_connect()
            mongo_db = mongo_client['mangamonster']
            tx_manga_errors = mongo_db['tx_manga_errors']
            tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
            manga_slug = manga['i']
            manga_ss = manga['ss']
            manga_url = f'https://mangasee123.com/manga/{manga_slug}'
            logging.info(manga_url)
            
            manga_soup = get_soup(manga_url, header=header)
            manga_name = manga_soup.find('meta', {'property': 'og:title'})[
                'content'].split('|')[0].strip()
            manga_thumb = manga_soup.find(
                'meta', {'property': 'og:image'})['content']
            regex = r'vm.Chapters\s=\s.{0,};'
            script = manga_soup.findAll('script')[-1].text
            list_chapters_str_regex = re.search(regex, script)
            bucket_manga = tx_manga_bucket_mapping.find_one({'original_id': manga_slug})
            if bucket_manga:
                bucket = bucket_manga['bucket']
            else:
                bucket = process_insert_bucket_mapping(manga_slug, tx_manga_bucket_mapping)
            if list_chapters_str_regex is None:
                print(f'{manga_url} error list_chapters_str_regex')
                return None
            list_chapters_str = list_chapters_str_regex.group()
            a = list_chapters_str.replace(
                'vm.Chapters = ', '').replace(';', '')
            list_chapters = a.strip('][').split('},')
            manga_count_chapters = len(list_chapters)
            list_chapters_info = []
            if '' not in list_chapters:
                for chapter in list_chapters:
                    chapter_json = self.string_to_json(chapter)
                    chapter_encoded = self.chapter_encode(
                        chapter_json['Chapter'])
                    chapter_url = 'https://mangasee123.com/read-online/{}{}.html'.format(
                        manga_slug, chapter_encoded)
                    chapter_source, chapter_info, index_name = self.get_chapter_info(
                        chapter_url)
                    chapter_info_dict = self.extract_chapter_info(
                        chapter_source, chapter_info, chapter_url, manga_slug, bucket)
                    list_chapters_info.append(chapter_info_dict)

            final_dict = {
                'name': manga_name,
                'original': manga_url,
                'original_id': manga_slug,
                'thumb': manga_thumb,
                'count_chapters': manga_count_chapters,
                'chapters': list_chapters_info,
                'manga_status':manga_ss,
                'source_site': MangaSourceEnum.MANGASEE.value
            }

            # Extract manga info
            manga_raw_info_dict = self.extract_manga_info(manga,manga_soup)
            logging.info('============%s' % manga_raw_info_dict)
            final_dict.update(manga_raw_info_dict)

            # Insert or Update
            filter_criteria = {"original_id": final_dict["original_id"]}
            mongo_collection.update_one(
                filter_criteria, {"$set": final_dict}, upsert=True)
            # mongo_collection.insert_one(final_dict)
        except Exception as ex:
            logging.info(str(ex))
            tx_manga_errors.insert_one({'type':ErrorCategoryEnum.MANGA_PROCESSING.name,'date':datetime.now(),'description':str(ex),'data': ''})

    def extract_chapter_info(self, chapter_source, chapter_info, chapter_url, manga_slug, bucket):
        formatted_chapter_number = format_leading_chapter(
            format_chapter_number(chapter_info['Chapter']))
        # Process chapter + chapter resources
        index_string = chapter_info['Chapter'][0:1]
        if index_string == '1':
            season = 0
        else:
            season = int(index_string)
        if chapter_info['Directory'] and chapter_info['Directory'] != '':
            directory = chapter_info['Directory']
            directory_slug = '-' + directory
        else:
            directory = ''
            directory_slug = ''
        # Generate resources:
        list_resources = []
        chapter_ordinal = format_chapter_number(chapter_info['Chapter'])
        chapter_number, chapter_part = process_chapter_ordinal(chapter_ordinal)
        chapter_season = format_leading_part(int(season))
        for i in range(1, int(chapter_info['Page']) + 1):
            img_url = self.get_image_url(slug=manga_slug, directory=directory,
                                              formatted_chapter_number=formatted_chapter_number, formatted_img_count=format_leading_img_count(i))
            list_resources.append(img_url)
        chapter_info_dict = {
            'ordinal':chapter_ordinal,
            'chapter_number':chapter_number,
            'chapter_part':chapter_part,
            'slug': manga_slug.lower() + directory_slug.lower() + '-chapter-' + format_chapter_number(chapter_info['Chapter']).replace('.', '-'),
            'original': chapter_url,
            'resource_status': 'ORIGINAL',
            'season': chapter_season,
            'resources': list_resources,
            'resources_storage': chapter_source,
            'resources_bucket': bucket,
            'pages': len(list_resources),
            'date': chapter_info['Date']
        }
        return chapter_info_dict

    def push_to_db(self, mode='manga', upload=False, count=None):
        new_process_push_to_db(mode, source_site=MangaSourceEnum.MANGASEE.value, upload=upload, count=count)

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
        soup = get_soup(url, header=header)
        return soup.find_all('script')[-1].text

    def get_image_url(self, slug, directory, formatted_chapter_number, formatted_img_count):
        if directory is not None:
            return '/manga/{}/{}/{}-{}.png'.format(slug, directory, formatted_chapter_number, formatted_img_count)
        else:
            return '/manga/{}/{}-{}.png'.format(slug, formatted_chapter_number, formatted_img_count)

    # def insert_db(self, db, chapter_obj, row_id, pages):

    #     chapter_query = db.query(MangaChapters).filter(MangaChapters.manga_id == row_id,
    #                                                    MangaChapters.slug == chapter_obj.slug, MangaChapters.season == chapter_obj.season)

    #     chapter_count = chapter_query.count()
    #     if chapter_count == 0:
    #         try:
    #             db.add(chapter_obj)
    #             db.commit()
    #         except Exception as ex:
    #             db.rollback()
    #     else:
    #         logging.info('CHAPTER EXISTS')

    #     # Check if chapter has resources
    #     db_chapter_obj = chapter_query.first()
    #     resource_count = db.query(MangaChapterResources).filter(
    #         MangaChapterResources.manga_chapter_id == db_chapter_obj.id).count()
    #     if resource_count == pages:
    #         return False
    #     return True
