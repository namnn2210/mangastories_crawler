from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import ErrorCategoryEnum, MangaSourceEnum
from utils.crawler_util import get_soup, process_insert_bucket_mapping, process_chapter_ordinal, format_leading_part
from connections.connection import Connection
from configs.config import MAX_THREADS
from datetime import datetime

import logging
import concurrent.futures
import re
import pytz


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76', 
    'Referer':'https://mangareader.to/'
}

class MangareaderCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Manhuaplus crawler created')
        return MangareaderCrawler()
    
class MangareaderCrawler(Crawler):
    
    def crawl(self):
        logging.info('Crawling all mangas from Mangareader...')
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_collection = mongo_db['tx_mangas']
        tx_manga_errors = mongo_db['tx_manga_errors']
        tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        
        # Crawl multiple pages
        list_manga_urls = self.get_all_manga_urls()
        
        logging.info('Total mangas: %s' % len(list_manga_urls))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(self.extract_manga_info, manga_url, mongo_collection, tx_manga_bucket_mapping, tx_manga_errors) for manga_url in list_manga_urls[:10]]
            
        for future in futures:
            future.result()
    
    
    def get_all_manga_urls(self):
        base_url = "https://mangareader.to/type/manhwa?sort=name-az"
        # Start with the initial URL
        current_url = base_url
        list_manga_urls = []
        while current_url:
            logging.info("Processing: %s " % current_url)
            list_mangas, current_url = self.process_page_urls(current_url)
            list_manga_urls += list_mangas
        return list_manga_urls
    
    def process_page_urls(self, url):
        list_mangas = []
        page_soup = get_soup(url,headers)
        manga_divs = page_soup.find_all('a',{'class':'manga-poster'})
        for manga in manga_divs:
            manga_url = 'https://mangareader.to' + manga['href']
            list_mangas.append(manga_url)
        next_page_link = page_soup.find('a', {'title': 'Next'})
        if next_page_link:
            next_page_url = 'https://mangareader.to' + next_page_link['href']
            return list_mangas, next_page_url
        return list_mangas, None
    
    def extract_manga_info(self,manga_url, mongo_collection, tx_manga_bucket_mapping, tx_manga_errors):
        try:
            logging.info(manga_url)
            manga_soup = get_soup(manga_url,headers)
            manga_original_id = manga_url.split('/')[-1].split('-')[0]
            manga_name = manga_soup.find('meta',{'property':'og-title'})
            manga_description = manga_soup.find('meta',{'property':'og-description'})
            manga_thumb = manga_soup.find('div',{'class':'anisc-poster'}).find('img')['src']
            manga_bucket = tx_manga_bucket_mapping.find_one({'original_id': manga_original_id})
            alternative_name_div = manga_soup('div', {'class':'manga-name-or'})
            if alternative_name_div:
                alternative_name = alternative_name_div.text
            else:
                alternative_name = ''
            if manga_bucket:
                bucket = manga_bucket['bucket']
            else:
                bucket = process_insert_bucket_mapping(manga_original_id, tx_manga_bucket_mapping)
            genre_div = manga_soup.find('div',{'class':'sort-desc'}).find('div',{'class':'genres'})
            genres = ','.join(genre.text for genre in genre_div.find_all('a'))
            info_div = manga_soup.find('div',{'class':'anisc-info'})
            list_processed_details = self.process_detail(info_div=info_div)
            
            list_chapters = manga_soup.find('ul',{'class':'reading-list'}).find_all('li',{'class':'chapter-item'})
            manga_count_chapters = len(list_chapters)
            
            list_chapters_info = []
            for chapter in list_chapters:
                    chapter_info_dict = self.extract_chapter_info(chapter=chapter, manga_slug=manga_original_id, bucket=bucket)
                    list_chapters_info.append(chapter_info_dict)
            final_dict = {
                'name':manga_name,
                'original':manga_url,
                'original_id': manga_original_id,
                'thumb':manga_thumb,
                'description':manga_description,
                'genre':genres,
                'count_chapters': manga_count_chapters, 
                'chapters': list_chapters_info,
                'official_translation':'',
                'rss':'',
                'alternative_name':alternative_name,
                'source_site':MangaSourceEnum.ASURATOON.value
            }
            for detail_dict in list_processed_details:
                key, value = next(iter(detail_dict.items()))
                final_dict[key] = value 
            # Insert or Update 
            filter_criteria = {"original_id": final_dict["original_id"]}
            mongo_collection.update_one(filter_criteria, {"$set": final_dict}, upsert=True)
        except Exception as ex:
            logging.info(str(ex))
            tx_manga_errors.insert_one({'type':ErrorCategoryEnum.MANGA_PROCESSING.name,'date':datetime.now(),'description':str(ex),'data': ''})
        
        
    def process_detail(self, info_div):
        list_processed_details = []
        for detail in info_div.find_all('div',{'class':'item-title'}):
            item_name = detail.find('span',{'class':'item-head'}).text
            if item_name == 'Type:':
                item_value = detail.find('a',{'class':'name'}).text
                list_processed_details.append({'type':item_value})
            if item_name == 'Status:':
                item_value = detail.find('span',{'class':'name'}).text
                list_processed_details.append({'status':item_value})
            if item_name == 'Published:':
                item_value = detail.find('span',{'class':'name'}).text
                list_processed_details.append({'published':item_value})
            if item_name == 'Authors:':
                item_value = ','.join(a.text for a in detail.find_all('a'))
                list_processed_details.append({'author':item_value})
        return list_processed_details
    
    def extract_chapter_info(self, chapter,manga_slug,bucket):
        chapter_url = 'https://mangareader.to' + chapter.find('a')['href']
        chapter_slug = manga_slug + '-' + chapter.find('a')['href'].split('/')[-1]
        chapter_soup = get_soup(chapter_url,headers)
        chapter_ordinal =  chapter['data-number']
        chapter_number, chapter_part = process_chapter_ordinal(chapter_ordinal)
        chapter_season = format_leading_part(0)
        reader_area = chapter_soup.find('div',{'class':'container-reader-chapter'})
        list_images = reader_area.find_all('div',{'class':'iv-card'})
        list_resources = []
        for image in list_images:
            original_url = image['data-url']
            regex_url = r'^(?:https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:\/\n\?\=]+)'
            chapter_source_match = re.search(regex_url, original_url)
            if chapter_source_match:
                chapter_source = chapter_source_match.group(1)
                img_url = original_url.replace(chapter_source_match.group(),'')
            else:
                img_url = original_url
            list_resources.append(img_url)
        chapter_info_dict = {
            'ordinal':chapter_ordinal,
            'chapter_number':chapter_number,
            'chapter_part':chapter_part,
            'slug':chapter_slug ,
            'original':chapter_url,
            'resource_status': 'ORIGINAL',
            'season':chapter_season,
            'pages':len(list_resources),
            'resources': list_resources,
            'resources_storage': chapter_source,
            'resources_bucket': bucket,
            'date':datetime.now(tz=pytz.timezone('America/Chicago'))
        }
        return chapter_info_dict
    
    def update_chapter(self):
        return super().update_chapter()
    
    def update_manga(self):
        return super().update_manga()
    
    def push_to_db(self, mode='manga', insert=True):
        return super().push_to_db(mode, insert)