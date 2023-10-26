import logging
import concurrent.futures

from connections.connection import Connection
from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import ErrorCategoryEnum, MangaSourceEnum
from utils.crawler_util import get_soup
from configs.config import MAX_THREADS

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76', 
    'Referer':'https://asuratoon.com/'
}

class AsuratoonCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Asuratoon crawler created')
        return AsuratoonCrawler()
    
class AsuratoonCrawler(Crawler):
    
    def crawl(self):
        logging.info('Crawling all mangas from Asuratoon...')
        
        # Crawl multiple pages
        list_manga_urls = self.get_all_manga_urls()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(self.extract_manga_info, manga_url) for manga_url in list_manga_urls]
            
        for future in futures:
            future.result()
            break

        
    def get_all_manga_urls(self):
        base_url = "https://asuratoon.com/manga/"
        initial_url = base_url + "?order=title"
        # Start with the initial URL
        current_url = initial_url
        list_manga_urls = []
        while current_url:
            logging.info("Processing: %s " % current_url)
            list_mangas, current_url = self.process_page_urls(current_url, base_url)
            list_manga_urls += list_mangas
            break
        return list_manga_urls
        
    # Define a function to parse and process a page
    def process_page_urls(self, url, base_url):
        list_mangas = []
        page_soup = get_soup(url,headers)
        manga_divs = page_soup.find_all('div',{'class':'bsx'})
        for manga in manga_divs:
            manga_url = manga.find('a')['href']
            list_mangas.append(manga_url)
        next_page_link = page_soup.find('div', {'class': 'hpage'}).find('a',{'class':'r'})
        if next_page_link:
            next_page_url = base_url + next_page_link['href']
            return list_mangas, next_page_url
        return list_mangas, None
    
    # Extract manga info
    def extract_manga_info(self,manga_url):
        logging.info(manga_url)
        manga_soup = get_soup(manga_url,headers)
        manga_slug = '-'.join(manga_url.split('/')[-2].split('-')[1:])
        manga_thumb = manga_soup.find('div',{'class':'thumb'}).find('img')['src']
        # Manga detail
        manga_description = manga_soup.find('div',{'itemprop':'description'}).find('p').text
        info_box = manga_soup.find('div',{'class':'infox'})
        list_details = info_box.find_all('div',{'class':'flex-wrap'})
        list_genres = info_box.find_all('div',{'class':'wd-full'})[1]
        
        list_processed_detail, list_processed_genres = self.process_detail(list_details,list_genres)
        
        # list_chapters = manga_soup.find('ul',{'class':'clstyle'}).find_all('li')
        # manga_count_chapters = len(list_chapters)
        
        # list_chapters_info = self.process_list_chapters(list_chapters=list_chapters)
        # final_dict = {'url': manga_slug,'count_chapters': manga_count_chapters, 'chapters': list_chapters_info, 'source_site':MangaSourceEnum.ASURATOON.value}
        # logging.info(final_dict)
        
    def process_detail(self, list_details, list_genres):
        list_processed_detail = []
        for detail in list_details:
            list_detail_info = detail.find_all('div',{'class':'fmed'})
            for info in list_detail_info:
                b_tag = info.find('b').text
                if b_tag == 'Posted On':
                    value = info.find('span').text
                    list_processed_detail.append({'published':value})
                    
                elif b_tag == 'Author':
                    value = info.find('span').text
                    list_processed_detail.append({'author':value})
        a_tags = list_genres.find_all('a')
        list_processed_genres = [tag.text for tag in a_tags]
        return list_processed_detail, list_processed_genres
        
    def process_list_chapters(self, list_chapters):
        list_chapters_info = []
        for chapter in list_chapters:
            chapter_num = chapter['data-num']
            chapter_url = chapter.find('div',{'class':'eph-num'}).find('a')['href']
            chapter_soup = get_soup(chapter_url,headers)
            reader_area = chapter_soup.find('div',{'id':'readerarea'})
            list_images = reader_area.find_all('img',{'decoding':'async'})
            list_image_urls = []
            for index, image in enumerate(list_images):
                list_image_urls.append({'img_count':index, 'img_url':image['src']})
            chapter_info_dict = {
                'chapter_num':chapter_num,
                'chapter_url':chapter_url,
                'image_urls':list_image_urls,
                'chapter_source': 'https://asuratoon.com'
            }
            list_chapters_info.append(chapter_info_dict)
        return list_chapters_info
    
    def update_chapter(self):
        return super().update_chapter()
    
    def update_manga(self):
        list_manga_urls = self.get_all_manga_urls()
        return super().update_manga()