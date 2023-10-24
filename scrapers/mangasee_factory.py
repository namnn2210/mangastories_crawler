from .base.crawler_factory import CrawlerFactory
from .mangasee import MangaseeCrawler

import logging

class MangaseeCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        print('Mangasee crawler created')
        return MangaseeCrawler()