from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import ErrorCategoryEnum, MangaSourceEnum
from utils.crawler_util import get_soup, parse_soup, process_insert_bucket_mapping, process_chapter_ordinal, format_leading_part, new_process_push_to_db
from connections.connection import Connection
from configs.config import MAX_THREADS
from datetime import datetime

import logging
import concurrent.futures
import re
import pytz
import requests


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76', 
    'Referer':'https://ww7.mangakakalot.tv/'
}

class MangakakalotCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Mangakakalot crawler created')
        return MangakakalotCrawler()
    
class MangakakalotCrawler(Crawler):

    def crawl(self, original_id=None):
        logging.info('Crawling all mangas from Mangakakalot...')
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_collection = mongo_db['tx_mangas']
        tx_manga_errors = mongo_db['tx_manga_errors']
        tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        
        # Crawl multiple pages
        list_manga_urls = self.get_all_manga_urls()
        
        logging.info('Total mangas: %s' % len(list_manga_urls))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(self.extract_manga_info, manga_url, mongo_collection, tx_manga_bucket_mapping, tx_manga_errors) for manga_url in list_manga_urls[:10]]
            
        for future in futures:
            future.result()
            
            
            
            
    def get_all_manga_urls(self):
        page = 1
        list_manga_urls = []
        list_starting_urls = []
        # Start with the initial URL
        while page <= 1671:
            base_url = f"https://ww7.mangakakalot.tv/manga_list/?type=topview&category=all&state=all&page={page}"
            list_starting_urls.append(base_url)
            page += 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
            futures = [executor.submit(self.process_get, starting_url) for starting_url in list_starting_urls]
        for future in futures:
            list_mangas = future.result()
            list_manga_urls += list_mangas
        return list_manga_urls
    
    def process_get(self, starting_url):
        logging.info("Processing: %s " % starting_url)
        list_mangas = self.process_page_urls(starting_url)
        return list_mangas
    
    def process_page_urls(self, url):
        list_mangas = []
        page_soup = get_soup(url,headers)
        list_manga_div = page_soup.find_all('div',{'class':'list-truyen-item-wrap'})
        for manga_div in list_manga_div:
            manga_href = manga_div.find('a')['href']
            manga_url = f'https://ww7.mangakakalot.tv{manga_href}'
            list_mangas.append(manga_url)
        return list_mangas
    
    def update_chapter(self):
        return super().update_chapter()
    
    def update_manga(self):
        return super().update_manga()
    
    def push_to_db(self, mode='manga', insert=True):
        return super().push_to_db(mode, insert)