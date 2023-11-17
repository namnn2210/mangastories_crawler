from sqlalchemy import null
from scrapers.mangasee import MangaseeCrawlerFactory
from scrapers.asuratoon import AsuratoonCrawlerFactory
from scrapers.manhuaplus import ManhuaplusCrawlerFactory 
from scrapers.mangareader import MangareaderCrawlerFactory
from utils import crawler_util
from sources.manga_sources import MangaSourceWriter

def create_and_run_crawler(factory):
    crawler = factory.create_crawler()
    crawler.crawl()
    
def push_not():
    from connections.connection import Connection
    from models.new_entities import NewManga
    db = Connection().mysql_connect()
    list_original_ids = [item[0] for item in db.query(NewManga.original_id).where(NewManga.name == '').where(NewManga.original_id is not null).all()]
    return list_original_ids

if __name__ == "__main__":
    # asuratoon = AsuratoonCrawlerFactory().create_crawler().push_to_db(mode='manga',count=20)
    # mangasee = MangaseeCrawlerFactory().create_crawler().push_to_db(mode='all')
    # manhuaplus = ManhuaplusCrawlerFactory().create_crawler().crawl()
    # mangareader = MangareaderCrawlerFactory().create_crawler().push_to_db()
    list_original_ids = push_not()
    # print(list_original_ids)
    mangasee = MangaseeCrawlerFactory().create_crawler().push_to_db(mode='update', type='all', list_update_original_id=list_original_ids)