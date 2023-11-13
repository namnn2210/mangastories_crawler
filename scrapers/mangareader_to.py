from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import ErrorCategoryEnum, MangaSourceEnum

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class MangareaderCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Manhuaplus crawler created')
        return MangareaderCrawler()
    
class MangareaderCrawler(Crawler):
    
    def crawl(self):
        return super().crawl()
    
    
    def get_all_manga_urls(self):
        base_url = "https://manhuaplus.com"
        # Start with the initial URL
        current_url = base_url
        list_manga_urls = []
        while current_url:
            logging.info("Processing: %s " % current_url)
            list_mangas, current_url = self.process_page_urls(current_url)
            list_manga_urls += list_mangas
        return list_manga_urls
    
    def update_chapter(self):
        return super().update_chapter()
    
    def update_manga(self):
        return super().update_manga()
    
    def push_to_db(self, mode='manga', insert=True):
        return super().push_to_db(mode, insert)