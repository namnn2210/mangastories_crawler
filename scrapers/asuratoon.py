import logging
import pytz
import concurrent.futures
import re

from connections.connection import Connection
from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from .base.enums import ErrorCategoryEnum, MangaSourceEnum
from models.entities import Manga
from utils.crawler_util import get_soup, format_leading_img_count,format_leading_part, process_chapter_ordinal,process_push_to_db, process_insert_bucket_mapping
from configs.config import MAX_THREADS
from datetime import datetime


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
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_collection = mongo_db['tx_mangas']
        tx_manga_errors = mongo_db['tx_manga_errors']
        tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
        
        # Crawl multiple pages
        list_manga_urls = self.get_all_manga_urls()
        
        logging.info('Total mangas: %s' % len(list_manga_urls))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(self.extract_manga_info, manga_url, mongo_collection, tx_manga_bucket_mapping, tx_manga_errors) for manga_url in list_manga_urls]
            
        for future in futures:
            future.result()

        
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
    def extract_manga_info(self,manga_url, mongo_collection, tx_manga_bucket_mapping, tx_manga_errors):
        try:
            logging.info(manga_url)
            manga_soup = get_soup(manga_url,headers)
            manga_slug = '-'.join(manga_url.split('/')[-2].split('-')[1:])
            
            manga_name = manga_soup.find('h1',{'class':'entry-title'}).text
            manga_thumb = manga_soup.find('div',{'class':'thumb'}).find('img')['src']
            manga_type_div = manga_soup.find('span',{'class':'type'})
            bucket_manga = tx_manga_bucket_mapping.find_one({'original_id': manga_slug})
            if bucket_manga:
                bucket = bucket_manga['bucket']
            else:
                bucket = process_insert_bucket_mapping(manga_slug, tx_manga_bucket_mapping)
            if manga_type_div is None:
                manga_type = ''
            else:
                manga_type = manga_type_div.text
            info_box = manga_soup.find('div',{'class':'infox'})
            list_details = info_box.find_all('div',{'class':'flex-wrap'})
            list_genres_div = info_box.find_all('div',{'class':'wd-full'})
            if len(list_genres_div) > 1:
                list_genres = list_genres_div[1]
            else:
                list_genres = None
            list_processed_detail, list_processed_genres = self.process_detail(list_details,list_genres)
    
            list_chapters = manga_soup.find('ul',{'class':'clstyle'}).find_all('li')
            manga_count_chapters = len(list_chapters)
            
            list_chapters_info = []
            non_chapter_number_count = 0
            for chapter in list_chapters:
                chapter_info_dict, non_chapter_number = self.extract_chapter_info(chapter=chapter, manga_slug=manga_slug, non_chapter_number_count=non_chapter_number_count, bucket=bucket)
                if non_chapter_number:
                    non_chapter_number_count += 1
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
                'type':manga_type,
                'alternative_name':'',
                'source_site':MangaSourceEnum.ASURATOON.value
            }
            description = manga_soup.find('div',{'itemprop':'description'}).find('p')
            if description is not None: 
                final_dict['description'] = description.text + ' (Source: Mangamonster.net)'
            else:
                final_dict['description'] = ''
            final_dict['genre'] = ','.join(list_processed_genres)
            for detail_dict in list_processed_detail:
                key, value = next(iter(detail_dict.items()))
                if key == 'author' and value == '-':
                    final_dict[key] = '' 
                else:
                    final_dict[key] = value 
            # Insert or Update 
            filter_criteria = {"original_id": final_dict["original_id"]}
            mongo_collection.update_one(filter_criteria, {"$set": final_dict}, upsert=True)
        # logging.info(final_dict)
        except Exception as ex:
            tx_manga_errors.insert_one({'type':ErrorCategoryEnum.MANGA_PROCESSING.name,'date':datetime.now(),'description':str(ex),'data': ''})
        
    def process_detail(self, list_details, list_genres):
        list_processed_detail = []
        for detail in list_details:
            list_detail_info = detail.find_all('div',{'class':'fmed'})
            for info in list_detail_info:
                b_tag = info.find('b').text
                if b_tag == 'Posted On':
                    value = info.find('span').text
                    list_processed_detail.append({'published':value.replace('\r','').replace('\t','').replace('\n','')})
                    
                elif b_tag == 'Author':
                    value = info.find('span').text
                    list_processed_detail.append({'author':value.replace('\r','').replace('\t','').replace('\n','')})
        if list_genres is not None:
            a_tags = list_genres.find_all('a')
            list_processed_genres = [tag.text for tag in a_tags]
        else:
            list_processed_genres = []
        return list_processed_detail, list_processed_genres
    
        
    def extract_chapter_info(self, chapter,manga_slug,non_chapter_number_count,bucket):
        chapter_url = chapter.find('div',{'class':'eph-num'}).find('a')['href']
        chapter_slug = '-'.join(chapter_url.split('/')[-2].split('-')[1:])
        chapter_soup = get_soup(chapter_url,headers)
        reader_area = chapter_soup.find('div',{'id':'readerarea'})
        list_images = reader_area.find_all('img',{'decoding':'async'})
        list_resources = []
        chapter_source = None
        str_chapter_num = chapter.find('span',{'class':'chapternum'}).text
        chapter_ordinal = self.process_chapter_number(str_chapter_num)
        if chapter_ordinal is None:
            chapter_ordinal = 0
        chapter_number, chapter_part = process_chapter_ordinal(chapter_ordinal)
        chapter_season = format_leading_part(0)
        for index, image in enumerate(list_images):
            original_url = image['src']
            regex_url = r'^(?:https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:\/\n\?\=]+)'
            chapter_source_match = re.search(regex_url, original_url)
            if chapter_source_match:
                chapter_source = chapter_source_match.group(1)
                img_url = original_url.replace(chapter_source_match.group(),'')
            # img_name = '{}.webp'.format(format_leading_img_count(index+1))
            # s3_url = '{}/{}/{}/{}/{}/{}'.format('storage', manga_slug.lower(),
            #                                     chapter_season, chapter_number, chapter_part, img_name)
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
        if chapter_ordinal is None:
            return chapter_info_dict, False
        return chapter_info_dict, True
    
    def process_chapter_number(self, str_chapter_num):
        regex = r'Chapter (\d+(\.\d+)?)'
        chapter_num_match = re.search(regex, str_chapter_num)
        if chapter_num_match:
            return chapter_num_match.group(1)
        else:
            return None
    
    def update_chapter(self):
        return super().update_chapter()
    
    def update_manga(self):
        list_manga_urls = self.get_all_manga_urls()
        db = Connection().mysql_connect()
        mongo_client = Connection().mongo_connect()
        mongo_db = mongo_client['mangamonster']
        mongo_collection = mongo_db['tx_mangas']
        list_manga_update = []
        for manga_url in list_manga_urls:
            manga_slug = '-'.join(manga_url.split('/')[-2].split('-')[1:])
            manga_query = db.query(Manga).where(Manga.slug == manga_slug)
            if manga_query.first() is None:
                list_manga_update.append(manga_url)
                
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [executor.submit(self.extract_manga_info, manga_url, mongo_collection) for manga_url in list_manga_urls]
            
        for future in futures:
            future.result()
        
    def push_to_db(self):
        # logging.info(MangaSourceEnum.ASURATOON.value)
        process_push_to_db(mode='all', source_site=MangaSourceEnum.ASURATOON.value, insert=True)