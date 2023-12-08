from scrapers.mangasee import MangaseeCrawlerFactory

if __name__ == "__main__":
    mangakakalot = MangaseeCrawlerFactory().create_crawler().push_to_db(type='chapter',slug_format=False,publish=True, count=2, new=False)
