from sqlalchemy import null
from scrapers.mangakakalot import MangakakalotCrawlerFactory

if __name__ == "__main__":
    mangakakalot = MangakakalotCrawlerFactory().create_crawler().push_to_db(type='all', slug_format=True, publish=True,
                                                                            count=6000, new=False, upload=True)
