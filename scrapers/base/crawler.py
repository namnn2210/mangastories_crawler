from abc import ABC, abstractmethod


class Crawler(ABC):
    @abstractmethod
    def crawl(self, original_id=None):
        pass

    @abstractmethod
    def update_chapter(self, new=True):
        pass

    @abstractmethod
    def update_manga(self):
        pass

    @abstractmethod
    def push_to_db(self, mode='crawl', type='manga', list_update_original_id=None, upload=False, count=None, new=True,
                   slug_format=True, publish=False, bulk=False):
        """  
            push_to_db mode: 
                1. manga: push manga info to mysql
                2. chapter: push chapter info to mysql 
                3. all: push both manga info and chapters info to mysql
        """
        pass

    def default_user_agent(self):
        """Get default user agent to whole project"""
        return 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
               ' Chrome/32.0.1667.0 Safari/537.36'
