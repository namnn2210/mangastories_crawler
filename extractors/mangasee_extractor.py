from .base.extractor import Extractor
from utils.crawler_util import get_soup
from scrapers.base.enums import MangaMonsterBucketEnum, ErrorCategoryEnum, MangaSourceEnum
from utils.crawler_util import get_soup, format_chapter_number, format_leading_chapter, format_leading_img_count, \
    format_leading_part, chapter_builder, process_chapter_ordinal, new_process_push_to_db, \
    process_insert_bucket_mapping, process_push_to_db, new_chapter_builder, new_push_chapter_to_db, push_chapter_to_db
from bs4 import BeautifulSoup
from datetime import datetime

import re
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36',
    'Origin': 'https://mangasee123.com'
}


class MangaseeExtractor(Extractor):
    def __init__(self):
        super().__init__()

    def extract_manga_info(self, source_site, *args):
        try:
            manga = args[0]
            manga_slug = manga['i']
            manga_ss = manga['ss']
            manga_url = f'https://mangasee123.com/manga/{manga_slug}'
            manga_soup = get_soup(manga_url, header=header)
            manga_name = manga_soup.find('meta', {'property': 'og:title'})[
                'content'].split('|')[0].strip()
            manga_thumb = manga_soup.find(
                'meta', {'property': 'og:image'})['content']
            regex = r'vm.Chapters\s=\s.{0,};'
            script = manga_soup.findAll('script')[-1].text
            list_chapters_str_regex = re.search(regex, script)
            bucket_manga = self.mongo_tx_manga_bucket_mapping.find_one(
                {'original_id': manga_slug})
            if bucket_manga:
                bucket = bucket_manga['bucket']
            else:
                bucket = process_insert_bucket_mapping(
                    manga_slug, self.mongo_tx_manga_bucket_mapping)
            if list_chapters_str_regex is None:
                logging.info(manga_soup)
                logging.info(f'{manga_url} error list_chapters_str_regex')
                return None
            list_chapters_str = list_chapters_str_regex.group()
            a = list_chapters_str.replace(
                'vm.Chapters = ', '').replace(';', '')
            list_chapters = a.strip('][').split('},')
            # manga_count_chapters = len(list_chapters)
            # list_chapters_info = []
            # if '' not in list_chapters:
            #     for chapter in list_chapters:
            #         chapter_json = self.string_to_json(chapter)
            #         chapter_encoded = self.chapter_encode(
            #             chapter_json['Chapter'])
            #         chapter_url = 'https://mangasee123.com/read-online/{}{}.html'.format(
            #             manga_slug, chapter_encoded)
            #         chapter_source, chapter_info, index_name = self.get_chapter_info(
            #             chapter_url)
            #         chapter_info_dict = self.extract_chapter_info(
            #             chapter_source, chapter_info, chapter_url, manga_slug, bucket)
            #         list_chapters_info.append(chapter_info_dict)
            final_dict = {
                'name': manga_name,
                'original': manga_url,
                'original_id': manga_slug,
                'thumb': manga_thumb,
                # 'count_chapters': manga_count_chapters,
                # 'chapters': list_chapters_info,
                'manga_status': manga_ss,
                'source_site': MangaSourceEnum.MANGASEE.value
            }

            # Extract manga info
            manga_raw_info_dict = self.get_manga_info(manga, manga_soup)
            final_dict.update(manga_raw_info_dict)

            logging.info(final_dict)

            # Insert or Update
            # filter_criteria = {"original_id": final_dict["original_id"]}
            # self.mongo_tx_mangas.update_one(
            #     filter_criteria, {"$set": final_dict}, upsert=True)
            # mongo_collection.insert_one(final_dict)
        except Exception as ex:
            logging.info(str(ex))
            # tx_manga_errors.insert_one({'type': ErrorCategoryEnum.MANGA_PROCESSING.name, 'date': datetime.now(
            # ), 'description': str(ex), 'data': ''})

    @staticmethod
    def get_manga_info(manga, manga_soup):
        list_group_flush = manga_soup.find('ul', {'class': 'list-group-flush'})
        info_group = list_group_flush.find_all(
            'li', {'class': 'list-group-item'})[2]
        manga_raw_info_dict = {'alternative_name': ','.join(manga['al']), 'author': ','.join(manga['a']),
                               'genre': ', '.join(manga['g']), 'published': manga['y'], 'manga_type': manga['t']}
        list_info = str(info_group).split("\n\n")
        for info in list_info[:-1]:
            new_info = info.strip(
                """ <li class="list-group-item {{vm.ShowInfoMobile ? '' : 'd-none d-md-block' }}"> """)
            new_info_soup = BeautifulSoup(new_info, 'html.parser')
            if new_info_soup.find('span') is not None:
                field = new_info_soup.find('span').text.replace(
                    '\n', '').replace('(s)', '').replace(':', '').lower()
                if len(new_info_soup.find_all('a')) > 0:
                    value = ','.join([x.text.strip('</')
                                      for x in new_info_soup.find_all('a')])
                else:
                    value = ' '.join(new_info_soup.find(
                        'div', {'class': 'top-5'}).text.strip('</').split())
                if field != 'status':
                    if field == 'description':
                        value = " ".join(value.split()) + \
                                ' (Source: Mangamonster.net)'
                        manga_raw_info_dict[field] = value
        return manga_raw_info_dict

    def extract_chapter_info(self, chapter_url, source_site, manga_original_id):
        print(chapter_url, source_site, manga_original_id)
