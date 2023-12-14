import logging
import concurrent.futures
import requests
import re
import pytz

from connections.connection import Connection
from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import ErrorCategoryEnum, MangaSourceEnum
from models.entities import Manga
from utils.crawler_util import get_soup, parse_soup, format_leading_part, process_chapter_ordinal, \
    new_process_push_to_db, \
    process_insert_bucket_mapping
from configs.config import MAX_THREADS
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76',
    'Referer': 'https://manhuaus.com/'
}


class ManhuausCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Manhuaus crawler created')
        return ManhuausCrawler()


class ManhuausCrawler(Crawler):

    def crawl(self, original_ids=None):
        logging.info('Crawling all mangas from Manhuaus...')
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_collection = mongo_db['tx_mangas']
        tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        tx_manga_errors = mongo_db['tx_manga_errors']

        # Crawl multiple pages
        list_manga_urls = self.get_all_manga_urls()

        logging.info('Total mangas: %s' % len(list_manga_urls))

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(self.extract_manga_info, manga_url, mongo_collection, tx_manga_bucket_mapping,
                                       tx_manga_errors)
                       for manga_url in list_manga_urls]

        for future in futures:
            future.result()

    def get_all_manga_urls(self):
        list_manga_urls = []
        page = 0
        list_mangas = self.process_page_urls(page)
        while len(list_mangas) > 0:
            list_manga_urls += list_mangas
            page += 1
            list_mangas = self.process_page_urls(page)
        return list_manga_urls

    # Define a function to parse and process a page
    def process_page_urls(self, page):
        list_mangas = []
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_url = 'https://manhuaus.com/wp-admin/admin-ajax.php'
        data_form = {
            'action': 'madara_load_more',
            'template': 'madara-core/content/content-archive',
            'page': page,
            'vars[paged]': '0',
            'vars[post_type]': 'wp-manga',
            'vars[posts_per_page]': '250'
        }
        response = requests.post(post_url, data=data_form, headers=headers).text
        page_soup = parse_soup(response)
        manga_url_divs = page_soup.find_all('h3', {'class': 'h5'})
        for div in manga_url_divs:
            manga_url = div.find('a')['href']
            list_mangas.append(manga_url)
        return list_mangas

    def extract_manga_info(self, manga_url, mongo_collection, tx_manga_bucket_mapping, tx_manga_errors):
        try:
            logging.info(manga_url)
            manga_soup = get_soup(manga_url, headers)
            manga_original_id = manga_url.split('/')[-2]

            # Thumb
            manga_thumb = manga_soup.find('meta', {'property': 'og:image'})['content']

            # Name
            manga_name = manga_soup.find('div', {'class': 'post-title'}).text.replace('\t', '').replace('\n',
                                                                                                        '').strip()

            # Description
            manga_description = manga_soup.find('meta', {'property': 'og:description'})['content']

            # Bucket
            manga_bucket = tx_manga_bucket_mapping.find_one({'original_id': manga_original_id})
            if manga_bucket:
                bucket = manga_bucket['bucket']
            else:
                bucket = process_insert_bucket_mapping(manga_original_id, tx_manga_bucket_mapping)

            manga_info = manga_soup.find('div', {'class': 'summary_content'}).find('div', {'class': 'post-content'})
            list_details = manga_info.find_all('div', {'class': 'post_content'})
            list_processed_detail = self.process_detail(list_details)

            list_chapters = manga_soup.find('ul', {'class': 'version-chap'}).find_all('li')
            manga_count_chapters = len(list_chapters)

            list_chapters_info = []
            for chapter in list_chapters:
                str_chapter_num = chapter.find('a').text
                chapter_info_dict = self.extract_chapter_info(chapter=chapter, str_chapter_num=str_chapter_num,
                                                              manga_slug=manga_original_id, bucket=bucket)
                list_chapters_info.append(chapter_info_dict)

            final_dict = {
                'name': manga_name,
                'original': manga_url,
                'original_id': manga_original_id,
                'thumb': manga_thumb,
                'count_chapters': manga_count_chapters,
                'chapters': list_chapters_info,
                'source_site': MangaSourceEnum.MANHUAPLUS.value
            }

            if manga_description:
                final_dict['description'] = manga_description + ' (Source: Mangamonster.net)'
            else:
                final_dict['description'] = ''

            for detail_dict in list_processed_detail:
                key, value = next(iter(detail_dict.items()))
                final_dict[key] = value
                # Insert or Update

            logging.info(final_dict)
            filter_criteria = {"original_id": final_dict["original_id"]}
            mongo_collection.update_one(filter_criteria, {"$set": final_dict}, upsert=True)
        except Exception as ex:
            logging.info(str(ex))
            tx_manga_errors.insert_one(
                {'type': ErrorCategoryEnum.MANGA_PROCESSING.name, 'date': datetime.now(), 'description': str(ex),
                 'data': ''})

    def process_detail(self, list_details):
        list_processed_detail = []
        for detail in list_details:
            detail_name = detail.find('div', {'class': 'summary-heading'}).text
            detail_value = detail.find('div', {'class': 'summary-content'}).text
            if detail_name.strip() == 'Alternative':
                list_processed_detail.append({'alternative_name': detail_value})
            elif detail_name.strip() == 'Author(s)':
                list_processed_detail.append({'author': detail_value})
            elif detail_name.strip() == 'Type':
                list_processed_detail.append({'type': detail_value})
            elif detail_name.strip() == 'Genre(s)':
                list_processed_detail.append({'genre': detail_value.strip()})
            elif detail_name.strip() == 'Release':
                list_processed_detail.append({'published': detail_value})
            elif detail_name.strip() == 'Status':
                list_processed_detail.append({'status': detail_value})
        return list_processed_detail

    def extract_chapter_info(self, chapter, str_chapter_num, manga_slug, bucket):
        chapter_url = chapter.find('a')['href']
        chapter_slug = chapter_url.split('/')[-3] + chapter_url.split('/')[-2]
        chapter_soup = get_soup(chapter_url, headers)
        list_resources = []
        chapter_source = None
        reader_area = chapter_soup.find('div', {'class': 'read-container'})
        list_images = reader_area.find_all('div', {'class': 'page-break'})
        list_image_urls = []
        # str_chapter_num = chapter.find('span',{'class':'chapternum'}).text
        chapter_ordinal = self.process_chapter_number(str_chapter_num)
        chapter_number, chapter_part = process_chapter_ordinal(chapter_ordinal)
        chapter_season = format_leading_part(0)
        for index, img_div in enumerate(list_images):
            image = img_div.find('img')
            original_url = image['data-src']
            regex_url = r'^(?:https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:\/\n\?\=]+)'
            chapter_source_match = re.search(regex_url, original_url)
            if chapter_source_match:
                chapter_source = chapter_source_match.group(1)
                img_url = original_url.replace(chapter_source_match.group(), '')
            # img_name = '{}.webp'.format(format_leading_img_count(index+1))
            # s3_url = '{}/{}/{}/{}/{}/{}'.format('storage', manga_slug.lower(),
            #                                     chapter_season, chapter_number, chapter_part, img_name)
            else:
                img_url = original_url
            list_resources.append(img_url)
        chapter_info_dict = {
            'ordinal': chapter_ordinal,
            'chapter_number': chapter_number,
            'chapter_part': chapter_part,
            'slug': chapter_slug,
            'original': chapter_url,
            'resource_status': 'ORIGINAL',
            'season': chapter_season,
            'pages': len(list_resources),
            'resources': list_resources,
            'resources_storage': chapter_source,
            'resources_bucket': bucket,
            'date': datetime.now(tz=pytz.timezone('America/Chicago'))
        }
        return chapter_info_dict

    def process_chapter_number(self, str_chapter_num):
        regex = r'Chapter (\d+(\.\d+)?)'
        chapter_num_match = re.search(regex, str_chapter_num)
        if chapter_num_match:
            return chapter_num_match.group(1)
        else:
            return None

    def update_chapter(self):
        return super().update_chapter()

    def update_manga(self):
        return super().update_manga()

    def push_to_db(self, mode='crawl', type='manga', list_update_original_id=None, upload=False, count=None, new=True,
                   slug_format=True, publish=False, bulk=False):
        pass
