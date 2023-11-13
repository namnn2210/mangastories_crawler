from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import ErrorCategoryEnum, MangaSourceEnum
from utils.crawler_util import get_soup
from connections.connection import Connection

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76', 
    'Referer':'https://mangareader.to/'
}

class MangareaderCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Manhuaplus crawler created')
        return MangareaderCrawler()
    
class MangareaderCrawler(Crawler):
    
    def crawl(self):
        logging.info('Crawling all mangas from Mangareader...')
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_collection = mongo_db['tx_mangas']
        tx_manga_errors = mongo_db['tx_manga_errors']
        tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        
        # Crawl multiple pages
        list_manga_urls = self.get_all_manga_urls()
        
        logging.info('Total mangas: %s' % len(list_manga_urls))
    
    
    def get_all_manga_urls(self):
        base_url = "https://mangareader.to/type/manhwa?sort=name-az"
        # Start with the initial URL
        current_url = base_url
        list_manga_urls = []
        while current_url:
            logging.info("Processing: %s " % current_url)
            list_mangas, current_url = self.process_page_urls(current_url)
            list_manga_urls += list_mangas
        return list_manga_urls
    
    def process_page_urls(self, url, base_url):
        list_mangas = []
        page_soup = get_soup(url,headers)
        manga_divs = page_soup.find_all('a',{'class':'manga-poster'})
        for manga in manga_divs:
            manga_url = 'https://mangareader.to' + manga['href']
            list_mangas.append(manga_url)
        next_page_link = page_soup.find('a', {'tile': 'Next'})['href']
        if next_page_link:
            next_page_url = 'https://mangareader.to' + next_page_link['href']
            return list_mangas, next_page_url
        return list_mangas, None
    
    def update_chapter(self):
        return super().update_chapter()
    
    def update_manga(self):
        return super().update_manga()
    
    def push_to_db(self, mode='manga', insert=True):
        return super().push_to_db(mode, insert)