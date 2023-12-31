from hmac import new

import concurrent.futures
import re
import json
import logging

from connections.connection import Connection
from .base.crawler_2 import Crawler
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
from workers.worker import process_manga

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36',
    'Origin': 'https://mangasee123.com'
}


class MangaseeCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Mangasee crawler created')
        return MangaseeCrawler2()


class MangaseeCrawler2(Crawler):
    def __init__(self):
        super().__init__()

    def get_all_manga_urls(self):
        logging.info('Crawling all mangas from Mangasee...')

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
            # for item in list_mangas:
            #     manga_slug = item['i']
            #     list_mangas_final.append(f'https://mangasee123.com/manga/{manga_slug}')

        futures = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            # Submit each manga for processing to the executor
            for manga in list_mangas_final:
                future = executor.submit(
                    self.manga_enqueue, MangaSourceEnum.MANGASEE.value, manga)
                futures.append(future)

    def manga_enqueue(self, source_site, *args):
        logging.info('Enqueue manga: %s - %s' % (source_site, *args))
        super().manga_enqueue(source_site, *args)

    def chapter_enqueue(self, chapter_url, source_site, manga_original_id):
        logging.info('Enqueue chapter: %s - %s - %s' % (chapter_url, source_site, manga_original_id))
        super().chapter_enqueue(chapter_url, source_site, manga_original_id)
        # super().chapter_enqueue(chapter_url, source_site, manga_original_id)

    def get_update_chapter(self):
        pass

    def get_update_manga(self):
        pass

    def sync_to_db(self, mode='crawl', type='manga', list_update_original_id=None, upload=False, count=None, new=True,
                   slug_format=True, publish=False, bulk=False):
        pass
