from abc import ABC, abstractmethod
from connections.connection import Connection

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class Extractor(ABC):
    @abstractmethod
    def extract_manga_info(self, manga_url, source_site):
        pass

    @abstractmethod
    def extract_chapter_info(self, chapter_url, source_site, manga_original_id):
        pass
