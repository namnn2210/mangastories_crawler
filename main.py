from scrapers.mangasee import MangaseeCrawlerFactory
from scrapers.asuratoon import AsuratoonCrawlerFactory
from scrapers.manhuaplus import ManhuaplusCrawlerFactory 
from scrapers.mangareader import MangareaderCrawlerFactory
from utils import crawler_util
from sources.manga_sources import MangaSourceWriter

def create_and_run_crawler(factory):
    crawler = factory.create_crawler()
    crawler.crawl()

if __name__ == "__main__":
    asuratoon = AsuratoonCrawlerFactory().create_crawler().crawl()
    # mangasee = MangaseeCrawlerFactory().create_crawler().push_to_db(mode='all',count=2)
    # manhuaplus = ManhuaplusCrawlerFactory().create_crawler().crawl()
    # mangareader = MangareaderCrawlerFactory().create_crawler().push_to_db()