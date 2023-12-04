from sqlalchemy import null
from scrapers.mangakakalot import MangakakalotCrawlerFactory

if __name__ == "__main__":
    mangakakalot = MangakakalotCrawlerFactory().create_crawler().crawl()
