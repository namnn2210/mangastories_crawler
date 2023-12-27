from scrapers.mangasee_2 import MangaseeCrawlerFactory

if __name__ == "__main__":
    mangasee_crawler = MangaseeCrawlerFactory().create_crawler()
    mangasee_crawler.get_all_manga_urls()
    # mangasee_crawler.push_to_db(type='all', slug_format=False, publish=True)
    # mangasee_crawler.push_to_db(type='all',new=False, slug_format=False, publish=True)
