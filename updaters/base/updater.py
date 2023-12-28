from abc import ABC, abstractmethod
from connections.connection import Connection

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class Updater(ABC):

    # def __init__(self):
    #     mongo_client = Connection().mongo_connect()
    #     mongo_db = mongo_client['mangamonster']
    #     mongo_tx_mangas = mongo_db['tx_mangas']
    #     mongo_tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
    #
    #     self.mongo_tx_mangas = mongo_tx_mangas
    #     self.mongo_tx_manga_bucket_mapping = mongo_tx_manga_bucket_mapping

    @abstractmethod
    def get_update_chapter(self):
        pass

