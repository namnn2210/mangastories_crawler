from scrapers.mangasee import MangaseeCrawlerFactory

if __name__ == "__main__":
    MangaseeCrawlerFactory().create_crawler().update_chapter(new=False)
