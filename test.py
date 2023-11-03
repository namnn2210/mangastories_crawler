from seleniumbase import BaseCase
import time
BaseCase.main(__name__, __file__)

class WebToonTest(BaseCase):
    def test_webtoon(self):
        self.open("https://www.webtoon.xyz/")
        time.sleep(6)
        print(self.get_page_source())