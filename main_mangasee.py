from scrapers.mangasee import MangaseeCrawlerFactory

if __name__ == "__main__":
    mangasee = MangaseeCrawlerFactory().create_crawler()
    mangasee.update_chapter()
