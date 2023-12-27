from connections.connection import Connection
from scrapers.mangakakalot import MangakakalotCrawlerFactory
from models.entities import Manga

def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


if __name__ == "__main__":
    db = Connection().mysql_connect(db_name='mangamonster_com')
    list_update_original_ids = [item[0] for item in db.query(Manga.slug_original).filter(Manga.original.like('%mangakakalot%'),Manga.status == 1).all()]
    mangakakalot = MangakakalotCrawlerFactory().create_crawler()

    # list_update_original_ids = ['manga-kt987976']
    list_part = list(divide_chunks(list_update_original_ids, 10))
    for part in list_part:
        mangakakalot.push_to_db(mode='update', list_update_original_id=part, type='all', new=False,
                                slug_format=True, upload=False, publish=True)
