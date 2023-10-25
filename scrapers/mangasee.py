from connections.connection import Connection
from .base.crawler import Crawler
from .base.crawler_factory import CrawlerFactory
from configs.config import MAX_THREADS
from utils.crawler_util import get_soup, save_to_json
import requests
import concurrent.futures
import re
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

header = {
    'User-Agent':'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'
}

class MangaseeCrawlerFactory(CrawlerFactory):
    def create_crawler(self):
        logging.info('Mangasee crawler created')
        return MangaseeCrawler()

class MangaseeCrawler(Crawler):

    def crawl(self):
        logging.info('Mangasee crawling...')
        list_manga_url = 'https://mangasee123.com/_search.php'
        list_manga_request = requests.post(list_manga_url).json()
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Submit each manga for processing to the executor
            futures = [executor.submit(self.extract_manga_info, manga) for manga in list_manga_request]

            # Wait for all tasks to complete and get the results
        for future in futures:
            future.result()
        
            
    def update_chapter(self):
        manga_url = 'https://mangasee123.com/'
        soup = get_soup(manga_url, header=header)
        script = soup.findAll('script')[-1].text
        regex = r'vm.HotUpdateJSON\s=\s.{0,};'
        match = re.search(regex, script)
        list_latest_json = []
        if match:
            latest_json_str = match.group().replace('vm.HotUpdateJSON = ', '').replace(';', '')
            list_latest_json = json.loads(latest_json_str)
        for item in list_latest_json:
            chapter_encoded = self.chapter_encode(item['Chapter'])
            chapter_url = 'https://mangasee123.com/read-online/{}{}-page-1.html'.format(item['IndexName'], chapter_encoded)
            # selected_df = df_mangas.loc[df_mangas['slug'] == item['IndexName'].lower()]
            # if not selected_df.empty:
            #     # logger.info(df_manga_chapter_update)
            #     selected_id = selected_df['id'].values[0]
            #     df_chapter_update = df_manga_chapter_update[df_manga_chapter_update['manga_id'] == selected_id]
            #     if not df_chapter_update.empty:
            #         current_update_datetime = pd.to_datetime(df_chapter_update['chapter_update_datetime'].values[0])
                    
            #         # current_update_datetime = datetime.strptime(df_chapter_update['chapter_update_datetime'].values[0], "%Y-%m-%d %H:%M:%S")
            #         # web_update_datetime = current_update_datetime.replace(pd.to_datetime(item['Date']))
            #         original_datetime = datetime.strptime(item['Date'], "%Y-%m-%dT%H:%M:%S%z")
            #         desired_output_format = "%Y-%m-%d %H:%M:%S"
            #         web_update_datetime = pd.to_datetime(original_datetime.strftime(desired_output_format))
            #         # web_update_datetime = datetime.strptime(item['Date'], "%Y-%m-%d %H:%M:%S")
            #         if web_update_datetime > current_update_datetime:
            #             logger.info('UPDATE FOR MANGA ID %s ' % selected_id)
            #             df_manga_chapter_update.loc[df_manga_chapter_update['manga_id'] == selected_id, 'chapter_update_datetime'] = item['Date']
            #             df_manga_chapter_update.loc[df_manga_chapter_update['manga_id'] == selected_id, 'chapter_number'] = item['Chapter']
            #             list_current_folder_str = df_manga_chapter_update.loc[df_manga_chapter_update['manga_id'] == selected_id]['list_current_folder'].values[0]
            #             if isinstance(list_current_folder_str, float):
            #                 list_current_folder = []
            #             else:
            #                 list_current_folder = list_current_folder_str.split(',')
            #             list_current_folder.append(item['Chapter'])
            #             remove_duplicate_current_folder = list(set(list_current_folder))
            #             new_list_current_folder = ','.join(remove_duplicate_current_folder)
            #             df_manga_chapter_update.loc[df_manga_chapter_update['manga_id'] == selected_id, 'list_current_folder'] = new_list_current_folder
            #             chapter_source, chapter_info, index_name = get_chapter_info(chapter_url)
            #             if chapter_info['Directory'] and chapter_info['Directory'] != '':
            #                 directory = chapter_info['Directory']
            #                 directory_slug = '-' + directory
            #                 directory_name = directory + ' - '
            #                 season_regex = r'\d'
            #                 season = int(re.search(season_regex, chapter_info['Directory']).group())
            #             else:
            #                 directory_slug = ''
            #                 directory_name = ''
            #                 season = 0
            #             manga_id = selected_df['id'].values[0]
            #             formatted_chapter_number = format_leading_chapter(format_chapter_number(chapter_info['Chapter']))
            #             chapter_dict = {
            #                 "name": '{}Chapter {}'.format(directory_name,
            #                                                 format_chapter_number(item['Chapter'])),
            #                 "slug": item['IndexName'].lower() + directory_slug.lower() + '-chapter-' + format_chapter_number(
            #                     item['Chapter']).replace(
            #                     '.',
            #                     '-'),
            #                 "original": chapter_url,
            #                 "published": item['Date'],
            #                 "manga_id": manga_id,
            #                 "ordinal": float(format_chapter_number(item['Chapter'])),
            #                 'resource_status':'STORAGE',
            #                 "season": season,
            #                 'status': 1,
            #                 'total_view': 0,
            #                 'created_by': 0,
            #                 'updated_by': 0,
            #                 'deleted_by': 0,
            #                 'created_at': item['Date'],
            #                 'updated_at': item['Date'],
            #             }
        
        
        
    def extract_manga_info(self,manga):
        try:
            # Connect MongoDB
            mongo_client = Connection().mongo_connect()
            mongo_db = mongo_client['mangamonster']
            mongo_collection = mongo_db['tx_mangas']
                
            manga_slug = manga['i']
            manga_url = f'https://mangasee123.com/manga/{manga_slug}'
            logging.info(manga_url)
            soup = get_soup(manga_url, header=header)
            regex = r'vm.Chapters\s=\s.{0,};'
            script = soup.findAll('script')[-1].text
            list_chapters_str_regex = re.search(regex, script)
            if list_chapters_str_regex is None:
                print(f'{manga_url} error list_chapters_str_regex')
                return None
            list_chapters_str = list_chapters_str_regex.group()
            a = list_chapters_str.replace('vm.Chapters = ', '').replace(';', '')
            list_chapters = a.strip('][').split('},')
            manga_count_chapters = len(list_chapters)
            list_chapters_info = []
            if '' not in list_chapters:
                for chapter in list_chapters:
                    chapter_json = self.string_to_json(chapter)   
                    chapter_encoded = self.chapter_encode(chapter_json['Chapter'])
                    chapter_url = 'https://mangasee123.com/read-online/{}{}.html'.format(manga_slug, chapter_encoded)
                    chapter_soup = get_soup(chapter_url, header=header)
                    chapter_script = chapter_soup.findAll('script')[-1].text
                    chapter_regex = r'vm.CurChapter\s=\s.{0,};'
                    chapter_source_regex = r'vm.CurPathName\s=\s.{0,};'
                    chapter_source_str_regex = re.search(chapter_source_regex, chapter_script)
                    chapter_source_str = chapter_source_str_regex.group()
                    chapter_source = chapter_source_str.replace('vm.CurPathName = ', '').replace(';', '').replace('"', '')
                    chapter_str = re.search(chapter_regex, chapter_script).group()
                    chapter_info = json.loads(chapter_str.replace('vm.CurChapter = ', '').replace(';', ''))
                    chapter_info_dict = {
                        'chapter_info': chapter_info, 
                        'chapter_source': chapter_source
                    }
                    list_chapters_info.append(chapter_info_dict)
                final_dict = {'url': manga_slug,'count_chapters': manga_count_chapters, 'chapters': list_chapters_info}
                
                # Insert or Update 
                filter_criteria = {"url": final_dict["url"]}
                mongo_collection.update_one(filter_criteria, {"$set": final_dict}, upsert=True)
                # mongo_collection.insert_one(final_dict)
                logging.info('%s INSERTED TO DB' % manga_url)
            mongo_client.close()
        except Exception as ex:
            logging.error(str(ex))
        
    def string_to_json(self, chapter_str):
        if not chapter_str.endswith('}'):
            chapter_str += '}'
        return json.loads(chapter_str)


    def chapter_encode(self, chapter_string):
        index = ''
        index_string = chapter_string[0:1]
        if index_string != '1':
            index = '-index-{}'.format(index_string)
        chapter = int(chapter_string[1:-1])
        odd = ''
        odd_string = chapter_string[len(chapter_string) - 1]
        if odd_string != '0':
            odd = '.{}'.format(odd_string)
        return '-chapter-{}{}{}'.format(chapter, odd, index)


    