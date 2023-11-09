from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from PIL import ImageFile, Image
from numpy import imag
from configs.config import WEBP_QUALITY
from hashids import Hashids
from io import BytesIO
from datetime import datetime
from models.entities import Manga, MangaChapters, MangaChapterResources
from scrapers.base.enums import MangaSourceEnum, ErrorCategoryEnum, MangaMonsterBucketEnum
from connections.connection import Connection

import pytz
import os
import requests
import json
import io
import logging
import math
import random


ImageFile.LOAD_TRUNCATED_IMAGES = True
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def get_soup(url, header):
    return BeautifulSoup(urlopen(Request(url=url, headers=header)), 'html.parser')


def save_to_json(file_name, json_dict):
    with open(f'json/{file_name}', 'r') as json_file:
        json.dump(json_dict, json_file)


def format_leading_chapter(chapter):
    try:
        if int(chapter) >= 10 or int(chapter) < 10:
            return str(chapter).zfill(4)
        if int(chapter) >= 100:
            return str(chapter).zfill(3)
        if int(chapter) >= 1000:
            return str(chapter).zfill(1)
    except ValueError as ex:
        float_chapter = float(chapter)
        return str(float_chapter).zfill(6)


def format_leading_part(chapter):
    return str(chapter).zfill(2)


def format_leading_img_count(img_count):
    if img_count >= 10 or img_count < 10:
        return str(img_count).zfill(3)
    if img_count >= 100:
        return str(img_count).zfill(1)


def format_decimal(x):
    return ('%.2f' % x).rstrip('0').rstrip('.')


def format_chapter_number(chapter):
    if chapter[-1] != '0':
        return '{}.{}'.format(int(chapter[1:-1]), chapter[-1])
    return str(int(chapter[1:-1]))


def hashidx(id):
    hashids = Hashids(
        salt='TIND', alphabet='abcdefghijklmnopqrstuvwxyz1234567890', min_length=7)
    return hashids.encode(id)


def resize_image(image, new_height):

    # Calculate the resizing factor based on the new height and original height
    original_width, original_height = image.size
    percentage_difference = (new_height - original_height) / original_height
    resizing_factor = 1 + percentage_difference

    # Calculate the new width
    new_width = int(original_width * resizing_factor)

    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.ANTIALIAS)

    return resized_image


def watermark_with_transparency_io(io_img, watermark_image_path):
    base_image = Image.open(io_img).convert('RGBA')
    width, height = base_image.size
    if height > 16383:
        base_image = resize_image(base_image, new_height=16383)
    watermark = Image.open(watermark_image_path).convert('RGBA')
    width, height = base_image.size
    w_width, w_height = watermark.size
    position = (width - w_width, height - w_height)
    transparent = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    transparent.paste(base_image, (0, 0))
    transparent.paste(watermark, position, mask=watermark)
    transparent = transparent.convert('RGB')
    img_byte_arr = io.BytesIO()
    transparent.save(img_byte_arr, format='webp', quality=WEBP_QUALITY)
    return img_byte_arr.getvalue()


def image_s3_upload(s3, s3_path, original_path, bucket):
    img = watermark_with_transparency_io(
        BytesIO(requests.get(original_path).content), 'watermark/new_watermark.png')
    logging.info(s3_path)
    s3.put_object(Bucket=bucket, Key=s3_path, Body=img,
                  ACL='public-read', ContentType='image/webp')
    
def process_chapter_ordinal(chapter_ordinal):
    frac, whole = math.modf(float(chapter_ordinal))
    round_frac = round(frac, 2)
    chapter_number = format_leading_chapter(int(whole))
    chapter_part = format_leading_part(int(round_frac * 10))

    return chapter_number, chapter_part

def manga_builder(manga_obj_dict):
    img = Image.open(BytesIO(requests.get(manga_obj_dict['thumb']).content))
    today = datetime.now()
    today_str = '{}/{}/{}'.format(str(today.year),
                                  str(today.month), str(today.day))
    thumb_path = 'images/manga/{}/{}.jpg'.format(
        today_str, manga_obj_dict['original_id'].lower())
    thumb_save_path = f'/www-data/mangamonster.com/storage/app/public/{thumb_path}'
    os.makedirs(os.path.dirname(thumb_save_path), exist_ok=True)
    img.convert('RGB').save(thumb_save_path)
    if manga_obj_dict['type'] == 'Manga':
        manga_type = 1
    elif manga_obj_dict['type'] == 'Manhua':
        manga_type = 2
    elif manga_obj_dict['type'] == 'Manhwa':
        manga_type = 3
    else:
        manga_type = 1
    manga_dict = {
        'name': manga_obj_dict['name'],
        'slug': manga_obj_dict['original_id'].lower(),
        'original': manga_obj_dict['original'],
        'thumb': thumb_path,
        'manga_type_id': manga_type,
        'status': 1,
        'description':manga_obj_dict['description'],
        'author':manga_obj_dict['author'],
        'genre':manga_obj_dict['genre'],
        'total_view': 0,
        'created_by': 0,
        'updated_by': 0,
        'deleted_by': 0,
        'created_at': datetime.now(tz=pytz.timezone('America/Chicago')),
        'updated_at': datetime.now(tz=pytz.timezone('America/Chicago')),
        'slug_original': manga_obj_dict['original_id']
    }

    manga_dict['search_text'] = manga_dict.get('name', '') + manga_dict.get(
        'description', '') + manga_dict.get('author', '') + manga_dict.get('genre', '')
    manga_dict['search_field'] = manga_dict.get(
        'name', '') + manga_obj_dict['type'] + manga_dict.get('author', '') + manga_dict.get('genre', '')

    return manga_dict


def chapter_builder(chapter_dict, manga_id):
    return  {
            "name": 'S{} - Chapter {}'.format(chapter_dict['season'], chapter_dict['ordinal']),
            "slug": chapter_dict['slug'],
            "original": chapter_dict['original'],
            "published": chapter_dict['date'],
            "manga_id": manga_id,
            "ordinal": chapter_dict['ordinal'],
            'resource_status': chapter_dict['resource_status'],
            "season": chapter_dict['season'],
            'status': 1,
            'total_view': 0,
            'created_by': 0,
            'updated_by': 0,
            'deleted_by': 0,
            'created_at': chapter_dict['date'],
            'updated_at': chapter_dict['date'],
        }


def resource_builder(resource_obj_dict, chapter_id, bucket):

    return {
        "name": '{}'.format(format_leading_img_count(resource_obj_dict['index'])),
        "slug": '{}'.format(format_leading_img_count(resource_obj_dict['index'])),
        "original": resource_obj_dict['original'],
        "thumb": resource_obj_dict['s3'].replace('storage/', ''),
        "manga_chapter_id": chapter_id,
        "ordinal": resource_obj_dict['index'],
        'storage': bucket,
        'status': 1,
        'created_at': datetime.now(tz=pytz.timezone('America/Chicago')),
        'updated_at': datetime.now(tz=pytz.timezone('America/Chicago')),
    }



def push_manga_to_db(db, manga):
    manga_dict = manga_builder(manga)
    manga_obj = Manga(**manga_dict)
    query_new_manga = db.query(Manga).where(
        Manga.slug == manga_dict['slug'])
    try:
        db.add(manga_obj)
        db.commit()
        logging.info('NEW MANGA INSERTED')
    except Exception as ex:
        db.rollback()

    query_new_manga = db.query(Manga).where(
        Manga.slug == manga_dict['slug'])
    new_manga = query_new_manga.first()
    if new_manga is not None:
        idx = hashidx(new_manga.id)
        update_value = {
            'idx': idx,
            'local_url': 'https://mangamonster.net/' + manga_dict['slug'].lower() + '-m' + idx
        }
        query_new_manga.update(update_value)
        db.commit()


def push_chapter_to_db(db, processed_chapter_dict, bucket, manga_id, insert=True, error=None):
    s3 = Connection().s3_connect()
    chapter_dict = processed_chapter_dict['chapter_dict']
    manga_chapter_obj = MangaChapters(**chapter_dict)

    chapter_query = db.query(MangaChapters).filter(MangaChapters.manga_id == manga_id,
                                                    MangaChapters.slug == manga_chapter_obj.slug, MangaChapters.season == manga_chapter_obj.season)
    
    chapter_count = chapter_query.count()
    if chapter_count == 0:
        try:
            db.add(manga_chapter_obj)
            db.commit()
        except Exception as ex:
            db.rollback()
    else:
        logging.info('CHAPTER EXISTS')
    if insert:
        logging.info('INSERT MODE')
        db_chapter_obj = chapter_query.first()
        resource_count = db.query(MangaChapterResources).filter( MangaChapterResources.manga_chapter_id == db_chapter_obj.id).count()
        if resource_count != processed_chapter_dict['pages']:
            image_urls = processed_chapter_dict['image_urls']
            logging.info('Adding resources for chapter id %s...' % db_chapter_obj.id)
            for image in image_urls:
                image_dict = resource_builder(image, db_chapter_obj.id, bucket)
                image_dict_obj = MangaChapterResources(**image_dict)
                # logging.info(image_dict)
                try:
                    db.add(image_dict_obj)
                    db.commit()
                except Exception as ex:
                    db.rollback()
                logging.info('Saving to s3...')
                try:
                    image_s3_upload(
                        s3=s3, s3_path=image['s3'], original_path=image['original'], bucket=bucket)
                except Exception as ex:
                    error.insert_one({'type':ErrorCategoryEnum.S3_UPLOAD,'date':datetime.now(),'description':str(ex),'data': image['s3'] + '=>' + image['original']})
                    


def process_push_to_db(mode='manga', source_site=MangaSourceEnum.MANGASEE.value, insert=True, count=10):
    # Connect DB
    db = Connection().mysql_connect()
    mongo_client = Connection().mongo_connect()
    mongo_db = mongo_client['mangamonster']
    tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
    tx_mangas = mongo_db['tx_mangas']
    logging.info('Getting data with source site: %s' % source_site)
    list_mangas = tx_mangas.find(
        {"source_site": source_site})
    for manga in list_mangas:
        # Check if manga in DB:
        existed_manga_query = db.query(Manga).where(
            Manga.slug == manga['original_id'].lower()).where(Manga.status == 1)
        if mode == 'manga' or mode == 'all':
            if existed_manga_query.first() is None:
                logging.info('Inserting manga: %s' % manga['original_id'])
                push_manga_to_db(db, manga)
                process_insert_bucket_mapping(manga['original_id'], tx_manga_bucket_mapping)
                logging.info('Manga inserted')
        if mode == 'chapter' or mode == 'all':
            logging.info('Inserting manga chapters for manga: %s' % manga['original_id'])
            existed_manga = existed_manga_query.first()
            logging.info(existed_manga.slug)
            bucket = tx_manga_bucket_mapping.find_one({'$or':[ {"original_id": existed_manga.slug_original}, {"original_id": existed_manga.slug_original.lower()}] })['bucket']
            if existed_manga is not None:
                    chapters = manga['chapters']
                    list_processed_chapter_dict = []
                    for chapter in chapters:
                        db_manga_chapter = db.query(MangaChapters).where(MangaChapters.manga_id == existed_manga.id).where(MangaChapters.ordinal == chapter['ordinal']).where(MangaChapters.season == chapter['season']).where(MangaChapters.status == 1).first()
                        if db_manga_chapter is None:
                            chapter_dict = chapter_builder(chapter, existed_manga.id)
                            list_processed_chapter_dict.append({'chapter_dict': chapter_dict, 'pages': len(chapter['image_urls']), 'image_urls': chapter['image_urls']})

                    # Insert to database
                    for processed_chapter_dict in list_processed_chapter_dict:
                        push_chapter_to_db(db, processed_chapter_dict,bucket,existed_manga.id, insert=insert)
    db.close()
    
def process_insert_bucket_mapping(original_id, tx_manga_bucket_mapping):
    list_buckets = [item.value for item in MangaMonsterBucketEnum]
    selected_bucket = random.choice(list_buckets)
    bucket_mapping_data = {
        'original_id': original_id,
        'bucket': selected_bucket
    }
    tx_manga_bucket_mapping.insert_one(bucket_mapping_data)
    return selected_bucket