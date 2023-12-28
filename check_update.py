from updaters.mangasee import MangaseeUpdater
from connections.connection import Connection
import logging
from scrapers.base.enums import MangaMonsterBucketEnum, ErrorCategoryEnum, MangaSourceEnum
from deepdiff import DeepDiff

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

if __name__ == "__main__":
    list_update = MangaseeUpdater().get_update_chapter()
    mongo_client = Connection().mongo_connect()
    mongo_db = mongo_client['mangamonster']
    mongo_tx_manga_update = mongo_db['tx_manga_update']
    update_object = mongo_tx_manga_update.find_one({'source_site': MangaSourceEnum.MANGASEE.value})
    if update_object:
        logging.info('Update object found in database')
        logging.info('Comparing update object...')
        list_db_update = update_object['list_update']
        diff = DeepDiff(list_db_update, list_update, ignore_order=True)
        if diff != {}:
            logging.info('Update object is different from database')



            logging.info('Updating database...')
            mongo_tx_manga_update.update_one({'source_site': MangaSourceEnum.MANGASEE.value},
                                             {'$set': {'list_update': list_update}})
        else:
            logging.info('Update object is the same as database')
    else:
        logging.info('No update object found in database')
        mongo_tx_manga_update.insert_one({'source_site': MangaSourceEnum.MANGASEE.value, 'list_update': list_update})
