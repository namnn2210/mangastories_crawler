from abc import ABC, abstractmethod
from connections.connection import Connection

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class Crawler(ABC):
    def __init__(self):
        # Connect MongoDB
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_tx_mangas = mongo_db['tx_mangas']

        self.manga_redis = Connection().redis_connect(db=2, queue_name='manga_queue')
        self.chapter_redis = Connection().redis_connect(db=2, queue_name='chapter_queue')
        self.mongo_tx_mangas = mongo_tx_mangas

    @abstractmethod
    def get_all_manga_urls(self):
        pass

    @abstractmethod
    def manga_enqueue(self, manga_url, source_site):
        pass
        # self.manga_redis.enqueue(self.extract_manga_info, args=(manga_url, source_site))

    @abstractmethod
    def chapter_enqueue(self, chapter_url, source_site, manga_original_id):
        pass
        # self.chapter_redis.enqueue(self.extract_chapter_info, args=(chapter_url, source_site, manga_original_id))

    @abstractmethod
    def extract_manga_info(self, manga_url, source_site):
        pass

    @abstractmethod
    def extract_chapter_info(self, chapter_url, source_site, manga_original_id):
        pass

    @abstractmethod
    def get_update_chapter(self):
        pass

    @abstractmethod
    def get_update_manga(self):
        pass

    @abstractmethod
    def sync_to_db(self, mode='crawl', type='manga', list_update_original_id=None, upload=False, count=None, new=True,
                   slug_format=True, publish=False, bulk=False):
        pass
