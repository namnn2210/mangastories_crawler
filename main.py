from scrapers.mangasee_factory import MangaseeCrawlerFactory

def create_and_run_crawler(factory):
    crawler = factory.create_crawler()
    crawler.crawl()

if __name__ == "__main__":
    website1_factory = MangaseeCrawlerFactory()
    create_and_run_crawler(website1_factory)