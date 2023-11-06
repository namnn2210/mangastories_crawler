import logging
import concurrent.futures

from connections.connection import Connection
from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import ErrorCategoryEnum, MangaSourceEnum
from models.entities import Manga
from utils.crawler_util import get_soup, format_leading_img_count,format_leading_part, process_chapter_ordinal
from configs.config import MAX_THREADS
from datetime import datetime
import pytz


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76', 
    'Referer':'https://manhuaplus.com/'
}

class ManhuaplusCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Manhuaplus crawler created')
        return ManhuaplusCrawler()
    
class ManhuaplusCrawler(Crawler):
    
    def crawl(self):
        logging.info('Crawling all mangas from Manhuaplus...')
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_collection = mongo_db['tx_mangas']
        
        # Crawl multiple pages
        list_manga_urls = self.get_all_manga_urls()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(self.extract_manga_info, manga_url, mongo_collection) for manga_url in list_manga_urls]
            
        for future in futures:
            future.result()
    
    def get_all_manga_urls(self):
        base_url = "https://manhuaplus.com"
        # Start with the initial URL
        current_url = base_url
        list_manga_urls = []
        while current_url:
            logging.info("Processing: %s " % current_url)
            list_mangas, current_url = self.process_page_urls(current_url)
            list_manga_urls += list_mangas
        return list_manga_urls
        
    # Define a function to parse and process a page
    def process_page_urls(self, url):
        list_mangas = []
        page_soup = get_soup(url,headers)
        manga_divs = page_soup.find_all('div',{'class':'item-thumb'})
        for manga in manga_divs:
            manga_url = manga.find('a')['href']
            list_mangas.append(manga_url)
        next_page_link = page_soup.find('a', {'rel': 'next'})
        if next_page_link:
            next_page_url = next_page_link['href']
            return list_mangas, next_page_url
        return list_mangas, None
    
    def extract_manga_info(self,manga_url, mongo_collection):
        logging.info(manga_url)
        manga_soup = get_soup(manga_url,headers)
        manga_slug = '-'.join(manga_url.split('/')[-2])
        manga_name = manga_soup.find('meta',{'property':'og-title'})
        if manga_name is None:
            manga_name = manga_soup.find('h5',{'class':'widget-title'}).find('a')['title']
        manga_thumb = manga_soup.find('meta',{'property':'og:image'})['content']
        # manga_type = 'Manhua'
        description = manga_soup.find('meta',{'property':'og:description'})
        list_details = manga_soup.find_all('div',{'class':'post-content_item'})
        list_processed_detail = self.process_detail(list_details)
        
        list_chapters = manga_soup.find('ul',{'class':'version-chap'}).find_all('li')
        manga_count_chapters = len(list_chapters)
        
        list_chapters_info = []
        for chapter in list_chapters:
            str_chapter_num = chapter.find('a').text
            chapter_info_dict = self.extract_chapter_info(chapter=chapter, str_chapter_num=str_chapter_num, manga_slug=manga_slug)
            list_chapters_info.append(chapter_info_dict)
        
        final_dict = {
            'name':manga_name,
            'original':manga_url,
            'original_id': manga_slug,
            'thumb':manga_thumb,
            'count_chapters': manga_count_chapters, 
            'chapters': list_chapters_info,
            'official_translation':'',
            'rss':'',
            'source_site':MangaSourceEnum.MANHUAPLUS.value
        }
        
        if description:
            final_dict['description'] = description['content'] + ' (Source: Mangamonster.net)'
        else:
            final_dict['description'] = ''
            
        for detail_dict in list_processed_detail:
            key, value = next(iter(detail_dict.items()))
            final_dict[key] = value 
        # Insert or Update 
        filter_criteria = {"original_id": final_dict["original_id"]}
        mongo_collection.update_one(filter_criteria, {"$set": final_dict}, upsert=True)
        
    def extract_chapter_info(self, chapter, str_chapter_num,manga_slug):
        chapter_url = chapter.find('a')['href']
        chapter_slug = chapter_url.split('/')[-3] + chapter_url.split('/')[-2]
        chapter_soup = get_soup(chapter_url,headers)
        reader_area = chapter_soup.find('div',{'class':'reading-content'})
        list_images = reader_area.find_all('div',{'class':'page-break'})
        list_image_urls = []
        # str_chapter_num = chapter.find('span',{'class':'chapternum'}).text
        chapter_ordinal = self.process_chapter_number(str_chapter_num)
        chapter_number, chapter_part = process_chapter_ordinal(chapter_ordinal)
        season_path = format_leading_part(0)
        for index, image in enumerate(list_images):
            original_url = image['src']
            img_name = '{}.webp'.format(format_leading_img_count(index+1))
            s3_url = '{}/{}/{}/{}/{}/{}'.format('storage', manga_slug.lower(),
                                                season_path, chapter_number, chapter_part, img_name)
            list_image_urls.append({
                'index':index,
                'original':original_url,
                's3':s3_url
            })
            list_image_urls.append({'img_count':index, 'img_url':image['src']})
        chapter_info_dict = {
            'ordinal':chapter_ordinal,
            'chapter_number':chapter_number,
            'chapter_part':chapter_part,
            'slug':chapter_slug ,
            'original':chapter_url,
            'resource_status': 'ORIGINAL',
            'season':0,
            'pages':len(list_image_urls),
            'image_urls':list_image_urls,
            'date':datetime.now(tz=pytz.timezone('America/Chicago'))
        }
        return chapter_info_dict
    
    def process_detail(self, list_details):
        list_processed_detail = []
        for detail in list_details:
            detail_name = detail.find('div',{'class':'summary-heading'}).text
            detail_value = detail.find('div',{'class':'summary-content'}).text
            if detail_name.strip() == 'Alternative':
                list_processed_detail.append({'alternative_name':detail_value})
            elif detail_name.strip() == 'Author(s)':
                list_processed_detail.append({'author':detail_value})
            elif detail_name.strip() == 'Type':
                list_processed_detail.append({'type':detail_value})
            elif detail_name.strip() == 'Genre(s)':
                list_processed_detail.append({'genre':detail_value.strip()})
            elif detail_name.strip() == 'Release':
                list_processed_detail.append({'published':detail_value})
            elif detail_name.strip() == 'Status':
                list_processed_detail.append({'status':detail_value})
        return list_processed_detail
    
    def process_chapter_number(self, chapter_url):
        regex = r'Chapter (\d+(\.\d+)?)'
        chapter_num_match = re.search(regex, str_chapter_num)
        if chapter_num_match:
            return chapter_num_match.group(1)
        else:
            return None
    
    
        
    def push_to_db(self, mode='manga', insert=True):
        return super().push_to_db(mode, insert)
    
    def update_chapter(self):
        return super().update_chapter()
    
    def update_manga(self):
        return super().update_manga()