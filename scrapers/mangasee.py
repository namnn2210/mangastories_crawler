from hmac import new

import concurrent.futures
import re
import json
import logging

from connections.connection import Connection
from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import MangaMonsterBucketEnum, ErrorCategoryEnum, MangaSourceEnum
from models.new_entities import NewManga
from configs.config import MAX_THREADS, S3_ROOT_DIRECTORY, INSERT_QUEUE
from utils.crawler_util import get_soup, format_chapter_number, format_leading_chapter, format_leading_img_count, \
    format_leading_part, chapter_builder, process_chapter_ordinal, new_process_push_to_db, \
    process_insert_bucket_mapping, process_push_to_db, new_chapter_builder, new_push_chapter_to_db, push_chapter_to_db
# from models.entities import Manga, MangaChapters, MangaChapterResources
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36',
    'Origin': 'https://mangasee123.com'
}


class MangaseeCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Mangasee crawler created')
        return MangaseeCrawler()


class MangaseeCrawler(Crawler):

    def crawl(self, original_ids=None):
        logging.info('Crawling all mangas from Mangasee...')
        # Connect MongoDB
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_collection = mongo_db['tx_mangas']

        list_mangas_final = []
        list_manga_url = 'https://mangasee123.com/search/'
        soup = get_soup(list_manga_url, header=header)
        script = soup.findAll('script')[-1].text
        directory_regex = r'vm.Directory\s=\s.{0,};'
        directory_match = re.search(directory_regex, script)
        if directory_match:
            directory_json_str = directory_match.group().replace(
                'vm.Directory = ', '').replace(';', '')
            list_mangas = json.loads(directory_json_str)
            list_mangas_final = list_mangas
        if original_ids:
            list_mangas_final = []
            for id in original_ids:
                for item in list_mangas:
                    if item.get('i') == id:
                        list_mangas_final.append(item)
            # list_mangas_final = [item for item in list_mangas if item.get('i') == original_id]

        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            # Submit each manga for processing to the executor
            for manga in list_mangas_final:
                future = executor.submit(
                    self.get_manga_info, manga, mongo_collection)
                futures.append(future)

        #     # Wait for all tasks to complete and get the results
        for future in futures:
            future.result()
            break

    def crawl_chapter(self, list_hot_update=None, publish=True):
        db = Connection().mysql_connect()
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        tx_manga_errors = mongo_db['tx_manga_errors']
        tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        for chapter in list_hot_update:
            existed_manga = db.query(NewManga).where(NewManga.original_id == chapter['IndexName']).first()
            if existed_manga:
                # bucket = tx_manga_bucket_mapping.find_one({'$or': [{"original_id": existed_manga.original_id}, {
                #     "original_id": existed_manga.original_id.lower()}]})['bucket']
                chapter_encoded,_ = self.chapter_encode(
                    chapter['Chapter'])
                chapter_url = 'https://mangasee123.com/read-online/{}{}.html'.format(
                    chapter['IndexName'], chapter_encoded)
                chapter_source, chapter_info, index_name = self.get_chapter_info(
                    chapter_url)
                chapter_info_dict = self.extract_chapter_info(
                    chapter_source, chapter_info, chapter_url, chapter['IndexName'], 'mangamonster')

                if chapter_info_dict:
                    # Update to new db
                    logging.info('UPDATE TO NEW DB')

                    chapter_dict_new = new_chapter_builder(
                        chapter_info_dict, existed_manga.id, source_site=MangaSourceEnum.MANGASEE.value, publish=publish)
                    new_push_chapter_to_db(
                        db, chapter_dict_new, 'mangamonster', existed_manga.id, existed_manga.slug, upload=False,
                        error=tx_manga_errors)

                    # Update to old db
                    logging.info('UPDATE TO old DB')
                    old_db = Connection().mysql_connect(db_name='mangamonster_com')
                    chapter_dict_old = chapter_builder(chapter_info_dict, existed_manga.id, publish=publish)
                    s3_prefix = 'storage/' + existed_manga.original_id.lower() + '/' + \
                                chapter_info_dict['season'] + '/' + chapter_info_dict['chapter_number'] + \
                                '/' + chapter_info_dict['chapter_part']
                    processed_chapter_dict = {'chapter_dict': chapter_dict_old, 'pages': chapter_info_dict['pages'],
                                              'resources': chapter_info_dict[
                                                  'resources'], 'resources_storage': chapter_info_dict['resources_storage'],
                                              's3_prefix': s3_prefix}
                    push_chapter_to_db(old_db, processed_chapter_dict, 'mangamonster', existed_manga.id,
                                       insert=True, upload=False, error=tx_manga_errors)

    def update_chapter(self):
        logging.info('Updating new chapters...')
        logging.info('Time: %s' % datetime.now())
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
            hot_update_str = hot_update_match.group().replace(
                'vm.HotUpdateJSON = ', '').replace(';', '')
            list_hot_update = json.loads(hot_update_str)
        if latest_json_match:
            latest_json_str = latest_json_match.group().replace(
                'vm.LatestJSON = ', '').replace(';', '')
            list_latest_json = json.loads(latest_json_str)
        list_update_json = list_hot_update + list_latest_json
        logging.info('Mangasee new update: %s' % len(list_update_json))
        self.crawl_chapter(list_update_json)

    def update_manga(self):
        logging.info('Updating new mangas...')

        manga_url = 'https://mangasee123.com/'
        soup = get_soup(manga_url, header=header)
        script = soup.findAll('script')[-1].text
        regex = r'vm.NewSeriesJSON\s=\s.{0,};'
        list_new_mangas_match = re.search(regex, script)
        if list_new_mangas_match:
            new_mangas_str = list_new_mangas_match.group().replace(
                'vm.NewSeriesJSON = ', '').replace(';', '')
            list_mangas = new_mangas_str.strip('][').split('},')
        list_new_original_ids = []
        for manga in list_mangas[:10]:
            manga_json = self.string_to_json(manga)
            list_new_original_ids.append(manga_json['IndexName'])
        self.crawl(original_ids=list_new_original_ids)
        self.push_to_db(mode='crawl', type='all',
                        list_update_original_id=list_new_original_ids, upload=True)

    def extract_manga_info(self, manga, manga_soup):
        list_group_flush = manga_soup.find('ul', {'class': 'list-group-flush'})
        info_group = list_group_flush.find_all(
            'li', {'class': 'list-group-item'})[2]
        manga_raw_info_dict = {}
        manga_raw_info_dict['alternative_name'] = ','.join(manga['al'])
        manga_raw_info_dict['author'] = ','.join(manga['a'])
        manga_raw_info_dict['genre'] = ', '.join(manga['g'])
        manga_raw_info_dict['published'] = manga['y']
        manga_raw_info_dict['manga_type'] = manga['t']
        list_info = str(info_group).split("\n\n")
        for info in list_info[:-1]:
            new_info = info.strip(
                """ <li class="list-group-item {{vm.ShowInfoMobile ? '' : 'd-none d-md-block' }}"> """)
            new_info_soup = BeautifulSoup(new_info, 'html.parser')
            if new_info_soup.find('span') is not None:
                field = new_info_soup.find('span').text.replace(
                    '\n', '').replace('(s)', '').replace(':', '').lower()
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
            bucket_manga = tx_manga_bucket_mapping.find_one(
                {'original_id': manga_slug})
            if bucket_manga:
                bucket = bucket_manga['bucket']
            else:
                bucket = process_insert_bucket_mapping(
                    manga_slug, tx_manga_bucket_mapping)
            if list_chapters_str_regex is None:
                logging.info(manga_soup)
                logging.info(f'{manga_url} error list_chapters_str_regex')
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
                    chapter_encoded,_ = self.chapter_encode(
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
                'manga_status': manga_ss,
                'source_site': MangaSourceEnum.MANGASEE.value
            }

            # Extract manga info
            manga_raw_info_dict = self.extract_manga_info(manga, manga_soup)
            final_dict.update(manga_raw_info_dict)

            # Insert or Update
            filter_criteria = {"original_id": final_dict["original_id"]}
            mongo_collection.update_one(
                filter_criteria, {"$set": final_dict}, upsert=True)
            # mongo_collection.insert_one(final_dict)
        except Exception as ex:
            logging.info(str(ex))
            tx_manga_errors.insert_one({'type': ErrorCategoryEnum.MANGA_PROCESSING.name, 'date': datetime.now(
            ), 'description': str(ex), 'data': ''})

    def extract_chapter_info(self, chapter_source, chapter_info, chapter_url, manga_slug, bucket):
        if chapter_info:
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
                                             formatted_chapter_number=formatted_chapter_number,
                                             formatted_img_count=format_leading_img_count(i))
                list_resources.append(img_url)
            chapter_info_dict = {
                'ordinal': chapter_ordinal,
                'chapter_number': chapter_number,
                'chapter_part': chapter_part,
                'slug': manga_slug.lower() + directory_slug.lower() + '-chapter-' + format_chapter_number(
                    chapter_info['Chapter']).replace('.', '-'),
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
        return None

    def push_to_db(self, mode='crawl', type='manga', list_update_original_id=None, upload=False, count=None, new=True,
                   slug_format=True, publish=False, bulk=False):
        if new:
            new_process_push_to_db(mode=mode, type=type, list_update_original_id=list_update_original_id,
                                   source_site=MangaSourceEnum.MANGASEE.value, upload=upload, count=count)
        else:
            process_push_to_db(
                mode=mode, type=type, list_update_original_id=list_update_original_id,
                source_site=MangaSourceEnum.MANGASEE.value, insert=True, upload=upload, slug_format=slug_format,
                publish=publish, count=count)

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
        return '-chapter-{}{}{}'.format(chapter, odd, index), chapter

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

