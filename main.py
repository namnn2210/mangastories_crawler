from scrapers.mangasee import MangaseeCrawlerFactory
from scrapers.asuratoon import AsuratoonCrawlerFactory

from sources.manga_sources import MangaSourceWriter

def create_and_run_crawler(factory):
    crawler = factory.create_crawler()
    crawler.crawl()

if __name__ == "__main__":
    asurcatoon = AsuratoonCrawlerFactory().create_crawler().crawl()