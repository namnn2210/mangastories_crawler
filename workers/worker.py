from connections.connection import Connection
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from rq import Queue

def insert_resources(manga_id, chapter_slug, thumb_format, original_format, page, date, storage):
    engine = Connection().get_connection()
    proc_connection = engine.raw_connection()
    cursor = proc_connection.cursor()
    cursor.callproc('p_generate_chapter_resources', [manga_id, chapter_slug, thumb_format, original_format,
                                                     page, date, storage])
    cursor.close()
    proc_connection.commit()


def insert_resources_copy(prefix_chapter, slug, chapter_name, raw_slug, resource_original, directory, page, weblink, date, storage, external, extension):
    engine = Connection().get_connection()
    proc_connection = engine.raw_connection()
    cursor = proc_connection.cursor()
    cursor.callproc('p_generate_chapter_resources_copy1', [prefix_chapter, slug,
                                                           chapter_name,
                                                           raw_slug,
                                                           resource_original, directory,
                                                           page, weblink, date, storage, external, extension])
    cursor.close()
    proc_connection.commit()

def missing_pages(prefix_chapter, slug, chapter_name, raw_slug, resource_original, directory, page, weblink, date, chapter_id):
    engine = Connection().get_connection()
    proc_connection = engine.raw_connection()
    cursor = proc_connection.cursor()
    cursor.callproc('p_fix_missing_pages', [prefix_chapter, slug,
                                            chapter_name,
                                            raw_slug,
                                            resource_original, directory,
                                            page, weblink, date, chapter_id])
    cursor.close()
    proc_connection.commit()

