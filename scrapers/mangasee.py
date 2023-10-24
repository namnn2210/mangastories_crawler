from .base.crawler import Crawler
from configs.config import MAX_THREADS
from utils.crawler_util import get_soup
import requests
import concurrent.futures
import re
import json
import logging


class MangaseeCrawler(Crawler):

    def crawl(self):
        print('Mangasee crawling...')
        list_manga_url = 'https://mangasee123.com/_search.php'
        list_manga_request = requests.post(list_manga_url).json()
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Submit each manga for processing to the executor
            futures = [executor.submit(self.extract_manga_info, manga) for manga in list_manga_request]

            # Wait for all tasks to complete and get the results
            results = [future.result() for future in concurrent.futures.as_completed(futures) if future.result() is not None]
            
    def update_chapter(self):
        manga_url = 'https://mangasee123.com/'
        
        return super().update_chapter()
        
        
    def extract_manga_info(self,manga):
        try:
            manga_slug = manga['i']
            manga_url = f'https://mangasee123.com/manga/{manga_slug}'
            logging.info(manga_url)
            header = {
                'User-Agent':'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'
            }
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
            print(final_dict)
            return final_dict
        except Exception as ex:
            return None
        
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


    