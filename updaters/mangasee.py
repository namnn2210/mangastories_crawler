from .base.updater import Updater
from utils.crawler_util import get_soup
from scrapers.base.enums import MangaMonsterBucketEnum, ErrorCategoryEnum, MangaSourceEnum
from utils.crawler_util import get_soup, format_chapter_number, format_leading_chapter, format_leading_img_count, \
    format_leading_part, chapter_builder, process_chapter_ordinal, new_process_push_to_db, \
    process_insert_bucket_mapping, process_push_to_db, new_chapter_builder, new_push_chapter_to_db, push_chapter_to_db
from datetime import datetime

import re
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36',
    'Origin': 'https://mangasee123.com'
}


class MangaseeUpdater(Updater):
    def __init__(self):
        super().__init__()

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
        return '-chapter-{}{}{}'.format(chapter, odd, index), chapter

    def get_update_chapter(self):
        logging.info('Updating new chapters...')
        logging.info('Time: %s' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        manga_url = 'https://mangasee123.com/'
        soup = get_soup(manga_url, header=header)
        script = soup.findAll('script')[-1].text
        regex_hot_update = r'vm.HotUpdateJSON\s=\s.{0,};'
        regex_latest_json = r'vm.LatestJSON\s=\s.{0,};'
        hot_update_match = re.search(regex_hot_update, script)
        latest_json_match = re.search(regex_latest_json, script)
        list_latest_json = []
        list_hot_update = []
        list_update_final = []
        if hot_update_match:
            hot_update_str = hot_update_match.group().replace(
                'vm.HotUpdateJSON = ', '').replace(';', '')
            list_hot_update = json.loads(hot_update_str)
        if latest_json_match:
            latest_json_str = latest_json_match.group().replace(
                'vm.LatestJSON = ', '').replace(';', '')
            list_latest_json = json.loads(latest_json_str)
        list_update_json = list_hot_update + list_latest_json
        for item in list_update_json:
            datetime_obj = datetime.fromisoformat(item['Date'])
            formatted_date = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
            chapter_encoded, chapter = self.chapter_encode(item['Chapter'])
            chapter_url = 'https://mangasee123.com/read-online/{}{}.html'.format(item['IndexName'], chapter_encoded)
            list_update_final.append(
                {'original_id': item['IndexName'], 'chapter_number': chapter, 'date': formatted_date,
                 'url': chapter_url})
        return list_update_final
