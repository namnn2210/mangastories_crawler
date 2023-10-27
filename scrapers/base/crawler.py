from abc import ABC, abstractmethod


class Crawler(ABC):
    @abstractmethod
    def crawl(self):
        pass
    
    @abstractmethod
    def update_chapter(self):
        pass
    
    @abstractmethod
    def update_manga(self):
        pass
    
    @abstractmethod
    def push_to_db(self):
        pass

    def default_user_agent(self):
        """Get default user agent to whole project"""
        return 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
               ' Chrome/32.0.1667.0 Safari/537.36'
