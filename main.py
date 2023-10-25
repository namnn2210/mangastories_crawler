from scrapers.mangasee_factory import MangaseeCrawlerFactory
from sources.manga_sources import MangaSourceWriter

def create_and_run_crawler(factory):
    crawler = factory.create_crawler()
    crawler.crawl()

if __name__ == "__main__":
    # website1_factory = MangaseeCrawlerFactory()
    # create_and_run_crawler(website1_factory)
    manga_source_writer = MangaSourceWriter()
    manga_source_writer.add_manga_source_relations()