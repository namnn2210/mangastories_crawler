import logging

from scrapers.mangasee_2 import MangaseeCrawlerFactory

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def process_manga(manga_url, source_site):
    if source_site == 'mangasee':
        mangasee_crawler = MangaseeCrawlerFactory.create_crawler()
        mangasee_crawler.extract_manga_info(manga_url,source_site)
