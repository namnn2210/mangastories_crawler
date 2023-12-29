from updaters.mangasee import MangaseeUpdater
from connections.connection import Connection
import logging
from scrapers.base.enums import MangaMonsterBucketEnum, ErrorCategoryEnum, MangaSourceEnum
from datetime import datetime
from deepdiff import DeepDiff

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

if __name__ == "__main__":
    logging.info('Time start: %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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
            different_items = []

            if 'iterable_item_added' in diff:
                added_items = diff['iterable_item_added']
                for key, value in added_items.items():
                    different_items.append(value)

            logging.info(different_items)
            logging.info('Updating database...')
            # mongo_tx_manga_update.update_one({'source_site': MangaSourceEnum.MANGASEE.value},
            #                                  {'$set': {'list_update': list_update}})
        else:
            logging.info('Update object is the same as database')
    else:
        logging.info('No update object found in database')
        mongo_tx_manga_update.insert_one({'source_site': MangaSourceEnum.MANGASEE.value, 'list_update': list_update})
    logging.info('Time end: %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
