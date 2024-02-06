# from scrapers.mangasee_2 import MangaseeCrawlerFactory
from scrapers.mangasee import MangaseeCrawlerFactory

if __name__ == "__main__":
    mangasee_crawler = MangaseeCrawlerFactory().create_crawler()
    # mangasee_crawler.crawl()
    # mangasee_crawler.push_to_db(type='chapter', slug_format=False, publish=True)
    mangasee_crawler.push_to_db(type='all', new=False, slug_format=False, publish=True)
