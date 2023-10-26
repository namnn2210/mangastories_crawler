import logging

from connections.connection import Connection
from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76', 
    'Referer':'https://manhuaus.com/'
}

class ManhuausCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Manhuaus crawler created')
        return ManhuausCrawler()
    
class ManhuausCrawler(Crawler):
    
    def crawl(self):
        logging.info('Crawling all mangas from Manhuaus...')
        return super().crawl()
    
    def update_chapter(self):
        return super().update_chapter()
    
    def update_manga(self):
        return super().update_manga()