from scrapers.base.enums import MangaSourceEnum
from sqlalchemy.dialects.mysql import insert
from connections.connection import Connection
from models.entities import MangaSource, Manga, MangaSourceRelations


class MangaSourceWriter:
    def __init__(self):
        pass

    def insert_to_db(self):
        sources = [{'name': member.name, 'slug': member.value} for member in MangaSourceEnum]
        db = Connection().mysql_connect()
        for source in sources:
            new_source = MangaSource(**source)
            source_query_obj = db.query(MangaSource).where(MangaSource.name == new_source.name)
            if source_query_obj.first() is None:
                db.add(new_source)
                db.commit()
        db.close()
        
    def add_manga_source_relations(self):
        db = Connection().mysql_connect()
        list_mangas = db.query(Manga).where(Manga.status == 1).where(Manga.original.like('%mangasee%'))
        for manga in list_mangas:
            new_manga_source_relation = MangaSourceRelations(**{'manga_id':manga.id,'source_id':1})
            db.add(new_manga_source_relation)
            db.commit()
        db.close()
    