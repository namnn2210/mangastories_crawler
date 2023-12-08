from re import I
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from PIL import ImageFile, Image
from numpy import imag
from configs.config import WEBP_QUALITY
from hashids import Hashids
from io import BytesIO
from datetime import datetime
from models.entities import Manga, MangaChapters, MangaChapterResources
from models.new_entities import NewManga, NewMangaChapters
from scrapers.base.enums import MangaSourceEnum, ErrorCategoryEnum, MangaMonsterBucketEnum
from connections.connection import Connection
from slugify import slugify
from sqlalchemy.dialects.mysql import insert

import pytz
import os
import requests
import json
import io
import logging
import math
import random
import re


ImageFile.LOAD_TRUNCATED_IMAGES = True
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def get_soup(url, header):
    return BeautifulSoup(urlopen(Request(url=url, headers=header)), 'html.parser')


def parse_soup(html_string):
    return BeautifulSoup(html_string, 'html.parser')


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


def new_manga_builder(manga_obj_dict, slug_format=False, publish=True):
    img = None
    try:
        img = Image.open(BytesIO(requests.get(
            manga_obj_dict['thumb']).content))
    except Exception as ex:
        logging.info('Error saving thumb img: %s' % str(ex))
    today = datetime.now()
    today_str = '{}/{}/{}'.format(str(today.year),
                                  str(today.month), str(today.day))
    thumb_path = 'images/manga/{}/{}.jpg'.format(
        today_str, manga_obj_dict['original_id'].lower())
    thumb_save_path = f'/www-data/mangamonster.com/storage/app/public/{thumb_path}'
    os.makedirs(os.path.dirname(thumb_save_path), exist_ok=True)
    if img:
        img.convert('RGB').save(thumb_save_path)
    if manga_obj_dict['manga_type'] == 'Manga':
        manga_type = 1
    elif manga_obj_dict['manga_type'] == 'Manhua':
        manga_type = 2
    elif manga_obj_dict['manga_type'] == 'Manhwa':
        manga_type = 3
    else:
        manga_type = 1
    if manga_obj_dict['manga_status'].lower() == 'ongoing':
        publish_status = 0
    else:
        publish_status = 1
    
    if slug_format:
        slug = slugify(manga_obj_dict['name'])
    else:
        slug = manga_obj_dict['original_id'].lower()
        
    if publish:
        status = 1
    else:
        status = 0
        
    search_content = re.sub('[^a-zA-Z0-9]', ' ', manga_obj_dict['name']) + ', ' + manga_obj_dict.get('alternative_name', '')+ ', ' + manga_obj_dict['author']+ ', ' + manga_obj_dict['genre']+ ', ' + manga_obj_dict.get('manga_type','manga').lower()


    manga_dict = {
        'name': manga_obj_dict['name'],
        'slug': slug,
        'alt_name': manga_obj_dict.get('alternative_name', ''),
        'original': manga_obj_dict['source_site'],
        'original_id': manga_obj_dict['original_id'],
        'thumb': thumb_path,
        'manga_type_id': manga_type,
        'publish_status': publish_status,
        'status': status,
        'published': manga_obj_dict['published'],
        'description': manga_obj_dict['description'],
        'manga_authors': manga_obj_dict['author'],
        'manga_genres': manga_obj_dict['genre'],
        'score': random.uniform(5, 10),
        'num_scoring_users': random.randint(10000, 1000000),
        'search_content':search_content,
        'total_view': 0,
        'created_by': 0,
        'updated_by': 0,
        'deleted_by': None,
        'created_at': datetime.now(tz=pytz.timezone('America/Chicago')),
        'updated_at': datetime.now(tz=pytz.timezone('America/Chicago')),
    }

    return manga_dict


def manga_builder(manga_obj_dict, slug_format=False, publish=True):
    logging.info('go to builder')
    img = Image.open(BytesIO(requests.get(manga_obj_dict['thumb']).content))
    today = datetime.now()
    today_str = '{}/{}/{}'.format(str(today.year),
                                  str(today.month), str(today.day))
    thumb_path = 'images/manga/{}/{}.jpg'.format(
        today_str, manga_obj_dict['original_id'].lower())
    thumb_save_path = f'/www-data/mangamonster.com/storage/app/public/{thumb_path}'
    os.makedirs(os.path.dirname(thumb_save_path), exist_ok=True)
    img.convert('RGB').save(thumb_save_path)
    if manga_obj_dict['manga_type'] == 'Manga':
        manga_type = 1
    elif manga_obj_dict['manga_type'] == 'Manhua':
        manga_type = 2
    elif manga_obj_dict['manga_type'] == 'Manhwa':
        manga_type = 3
    else:
        manga_type = 1
    logging.info('==================== slug_format %s' % slug_format)
    if slug_format:
        slug = slugify(manga_obj_dict['name'])
    else:
        slug = manga_obj_dict['original_id'].lower()
    if publish:
        status = 1
    else:
        status = 0
    manga_dict = {
        'name': manga_obj_dict['name'],
        'slug': slug,
        'original': manga_obj_dict['original'],
        'thumb': thumb_path,
        'manga_type_id': manga_type,
        'status': status,
        'description': manga_obj_dict['description'],
        'author': manga_obj_dict['author'],
        'genre': manga_obj_dict['genre'],
        'total_view': 0,
        'created_by': 0,
        'updated_by': 0,
        'deleted_by': None,
        'created_at': datetime.now(tz=pytz.timezone('America/Chicago')),
        'updated_at': datetime.now(tz=pytz.timezone('America/Chicago')),
        'slug_original': manga_obj_dict['original_id']
    }

    manga_dict['search_text'] = manga_dict.get('name', '') + manga_dict.get(
        'description', '') + manga_dict.get('author', '') + manga_dict.get('genre', '')
    manga_dict['search_field'] = manga_dict.get(
        'name', '') + manga_obj_dict['manga_type'] + manga_dict.get('author', '') + manga_dict.get('genre', '')

    return manga_dict


def new_chapter_builder(chapter_dict, manga_id, source_site, publish=True):
    if chapter_dict['season'] == '00':
        name = 'Chapter {}'.format(chapter_dict['ordinal'])
    else:
        name = 'S{} - Chapter {}'.format(
            chapter_dict['season'], chapter_dict['ordinal'])
    if publish:
        status = 1
    else:
        status = 0
    return {
        "name": name,
        "slug": chapter_dict['slug'],
        "original": source_site,
        "manga_id": manga_id,
        "ordinal": chapter_dict['ordinal'],
        'chapter_no': chapter_dict['chapter_number'],
        'chapter_part': chapter_dict['chapter_part'],
        'season': chapter_dict['season'],
        'chapter_code': chapter_dict['chapter_number'] + chapter_dict['chapter_part'] + chapter_dict['season'],
        'original_id': chapter_dict['original'],
        'ordinal': chapter_dict['ordinal'],
        'published': chapter_dict['date'],
        'resources': chapter_dict['resources'],
        'resource_storage': chapter_dict['resources_storage'],
        'resource_total': chapter_dict['pages'],
        'resource_bucket': chapter_dict['resources_bucket'],
        'status': status,
        'total_view': 0,
        'created_by': 0,
        'updated_by': 0,
        'deleted_by': None,
        'created_at': chapter_dict['date'],
        'updated_at': chapter_dict['date'],
    }


def chapter_builder(chapter_dict, manga_id, publish=True):
    if chapter_dict['season'] == '00':
        name = 'Chapter {}'.format(chapter_dict['ordinal'])
    else:
        name = 'S{} - Chapter {}'.format(
            chapter_dict['season'], chapter_dict['ordinal'])
    if publish:
        status = 1
    else:
        status = 0
    return {
        "name": name,
        "slug": chapter_dict['slug'],
        "original": chapter_dict['original'],
        "published": chapter_dict['date'],
        "manga_id": manga_id,
        "ordinal": chapter_dict['ordinal'],
        'resource_status': chapter_dict['resource_status'],
        "season": chapter_dict['season'],
        'status': status,
        'total_view': 0,
        'created_by': 0,
        'updated_by': 0,
        'deleted_by': None,
        'created_at': chapter_dict['date'],
        'updated_at': chapter_dict['date'],
    }


def resource_builder(index, original, s3_path, chapter_id, bucket):

    return {
        "name": '{}'.format(format_leading_img_count(index)),
        "slug": '{}'.format(format_leading_img_count(index)),
        "original": original,
        "thumb": s3_path,
        "manga_chapter_id": chapter_id,
        "ordinal": index,
        'storage': bucket,
        'status': 1,
        'created_at': datetime.now(tz=pytz.timezone('America/Chicago')),
        'updated_at': datetime.now(tz=pytz.timezone('America/Chicago')),
    }


def push_manga_to_db(db, manga, slug_format=False, publish=True):
    manga_dict = manga_builder(manga,slug_format,publish)
    logging.info('=================== %s' % manga_dict)
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


def new_push_manga_to_db(db, manga, tx_manga_bucket_mapping, slug_format=False, publish=True):
    manga_dict = new_manga_builder(manga, slug_format,publish)
    manga_obj = NewManga(**manga_dict)
    query_new_manga = db.query(NewManga).where(
        NewManga.original_id == manga_dict['original_id'])
    existed_new_manga = query_new_manga.first()
    if existed_new_manga:
        del manga_dict['thumb']
        del manga_dict['score']
        del manga_dict['num_scoring_users']
        del manga_dict['status']
        manga_dict['idx'] = hashidx(existed_new_manga.id)
        for key, value in manga_dict.items():
            if key != 'thumb' and key != 'created_at':
                setattr(existed_new_manga, key, value)
        db.commit()
    else:
        try:
            db.add(manga_obj)
            db.commit()
            logging.info('NEW MANGA INSERTED')
            process_insert_bucket_mapping(
                manga['original_id'], tx_manga_bucket_mapping)

            new_manga = query_new_manga.first()
            if new_manga is not None:
                idx = hashidx(new_manga.id)
                new_manga.idx = idx
                db.commit()
        except Exception as ex:
            db.rollback


def new_push_chapter_to_db(db, processed_chapter_dict, bucket, manga_id, manga_slug, upload=True, error=None):
    s3 = Connection().s3_connect()
    # chapter_dict = processed_chapter_dict
    manga_chapter_obj = NewMangaChapters(**processed_chapter_dict)
    logging.info('Select chapter with manga_id %s and ordinal %s' %
                 (manga_id, manga_chapter_obj.ordinal))
    chapter_query = db.query(NewMangaChapters).filter(
        NewMangaChapters.manga_id == manga_id, NewMangaChapters.ordinal == float(manga_chapter_obj.ordinal))
    chapter_count = chapter_query.count()
    logging.info('Select count %s' % (chapter_count))
    if chapter_count == 0:
        try:
            db.add(manga_chapter_obj)
            db.commit()

            # Update idx after insert

            new_manga_chapter = chapter_query.first()
            if new_manga_chapter is not None:
                idx = hashidx(new_manga_chapter.id)
                new_manga_chapter.idx = idx
                # new_manga_chapter.update(update_value)
                db.commit()
                
                
            # Update last update
                
            manga_query = db.query(NewManga).filter(NewManga.id == manga_id).first()
            if manga_query:
                manga_query.latest_chapter_published = manga_chapter_obj.created_at
                db.commit()
                
        except Exception as ex:
            db.rollback()
    else:
        logging.info("Update chapter info")
        existed_chapter = chapter_query.first()
        processed_chapter_dict['idx'] = hashidx(existed_chapter.id)
        for key, value in processed_chapter_dict.items():
            if key != 'created_at':
                setattr(existed_chapter, key, value)
        db.commit()

    if upload:
        logging.info('Adding resources for chapter id %s...' %
                     chapter_query.first().id)
        index = 0
        while index < processed_chapter_dict['resource_total']:
            original = 'https://' + \
                processed_chapter_dict['resources_storage'] + \
                processed_chapter_dict['resources'][index]
            s3_prefix = manga_slug + '/' + \
                processed_chapter_dict['season'] + '/' + processed_chapter_dict['chapter_number'] + \
                '/' + processed_chapter_dict['chapter_part']
            img_count = index+1
            s3_path = s3_prefix + '/' + \
                format_leading_img_count(img_count) + '.webp'
            try:
                image_s3_upload(s3=s3, s3_path=s3_path,
                                original_path=original, bucket=bucket)
            except Exception as ex:
                error.insert_one({'type': ErrorCategoryEnum.S3_UPLOAD, 'date': datetime.now(
                ), 'description': str(ex), 'data': original + '=>' + s3_path})

def new_push_chapter_to_db_bulk(db, list_chapter_dict, bucket, manga_id, manga_slug, upload=True, error=None):
    # s3 = Connection().s3_connect()
    logging.info('Inserting %s chapters with manga_id %s ' %(len(list_chapter_dict), manga_id))
    stmt = insert(NewMangaChapters).values(list_chapter_dict)
    do_update_stmt = stmt.on_duplicate_key_update({
        "name": stmt.inserted.name,
        "slug": stmt.inserted.slug,
        "original": stmt.inserted.original,
        "manga_id": stmt.inserted.manga_id,
        "ordinal": stmt.inserted.ordinal,
        'chapter_no': stmt.inserted.chapter_no,
        'chapter_part': stmt.inserted.chapter_part,
        'season': stmt.inserted.season,
        'chapter_code': stmt.inserted.chapter_code,
        'original_id': stmt.inserted.original_id,
        'ordinal': stmt.inserted.ordinal,
        'published': stmt.inserted.published,
        'resources': stmt.inserted.resources,
        'resource_storage': stmt.inserted.resource_storage,
        'resource_total': stmt.inserted.resource_total,
        'resource_bucket': stmt.inserted.resource_bucket,
        'status': stmt.inserted.status,
        'total_view': stmt.inserted.total_view,
        'created_by': stmt.inserted.created_by,
        'updated_by': stmt.inserted.updated_by,
        'deleted_by': stmt.inserted.deleted_by,
        'created_at': stmt.inserted.created_at,
        'updated_at': stmt.inserted.updated_at,
    }
    )
    db.execute(do_update_stmt)
    db.commit()

def push_chapter_to_db(db, processed_chapter_dict, bucket, manga_id, insert=True, upload=True, error=None):
    s3 = Connection().s3_connect()
    chapter_dict = processed_chapter_dict['chapter_dict']
    manga_chapter_obj = MangaChapters(**chapter_dict)
    resources = []
    # resources_s3 = []
    index = 0
    while index < processed_chapter_dict['pages']:
        original = 'https://' + processed_chapter_dict['resources_storage'] + processed_chapter_dict['resources'][index]
        img_count = index+1
        # s3_path = processed_chapter_dict['s3_prefix'] + '/' + format_leading_img_count(img_count) + '.webp'
        # s3_url = f'https://{bucket}.ams3.digitaloceanspaces.com/{s3_path}'
        logging.info(original)
        # logging.info(s3_url)
        resources.append(original)
        # resources_s3.append(s3_url)
        index += 1
        
    manga_chapter_obj.resources = resources
    # manga_chapter_obj.resources_s3 = resources_s3
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
        logging.info('CHAPTER EXISTS => UPDATE')
        existed_chapter = chapter_query.first()
        for key, value in chapter_dict.items():
            if key != 'created_at':
                setattr(existed_chapter, key, value)
        existed_chapter.resources = resources
        # existed_chapter.resources_s3 = resources_s3
        
        logging.info('%s => %s ' % (existed_chapter.resource_status, chapter_dict['resource_status']))
        db.commit()
        
    # Update last update         
    manga_query = db.query(Manga).filter(Manga.id == manga_id).first()
    if manga_query:
        manga_query.latest_chapter_published = manga_chapter_obj.created_at
        db.commit()
        
    # if insert:
    #     logging.info('INSERT MODE')
    #     db_chapter_obj = chapter_query.first()
    #     resource_count = db.query(MangaChapterResources).filter(
    #         MangaChapterResources.manga_chapter_id == db_chapter_obj.id).count()
    #     if resource_count != processed_chapter_dict['pages']:
    #         # image_urls = processed_chapter_dict['image_urls']
    #         logging.info('Adding resources for chapter id %s...' %
    #                      db_chapter_obj.id)
    #         index = 0
            # while index < processed_chapter_dict['pages']:
            #     original = 'https://' + \
            #         processed_chapter_dict['resources_storage'] + \
            #         processed_chapter_dict['resources'][index]
            #     img_count = index+1
            #     s3_path = processed_chapter_dict['s3_prefix'] + \
            #         '/' + format_leading_img_count(img_count) + '.webp'
            #     image_dict = resource_builder(
            #         img_count, original, s3_path, db_chapter_obj.id, bucket)
            #     image_dict_obj = MangaChapterResources(**image_dict)
            #     # logging.info(image_dict)
            #     try:
            #         db.add(image_dict_obj)
            #         db.commit()
            #     except Exception as ex:
            #         db.rollback()
            #     logging.info('Saving to s3...')
            #     if upload:
            #         try:
            #             image_s3_upload(
            #                 s3=s3, s3_path=s3_path, original_path=original, bucket=bucket)
            #         except Exception as ex:
            #             error.insert_one({'type': ErrorCategoryEnum.S3_UPLOAD, 'date': datetime.now(
            #             ), 'description': str(ex), 'data': original + '=>' + s3_path})
            #     index += 1


def new_process_push_to_db(mode='crawl', type='manga', list_update_original_id=None, source_site=MangaSourceEnum.MANGASEE.value, upload=True, count=None, slug_format=False, publish=True, bulk=False):
    db = Connection().mysql_connect()
    mongo_client = Connection().mongo_connect()
    mongo_db = mongo_client['mangamonster']
    tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
    tx_mangas = mongo_db['tx_mangas']
    tx_manga_errors = mongo_db['tx_manga_errors']
    logging.info('Getting data with source site: %s' % source_site)
    if count:
        list_mangas = tx_mangas.find({"source_site": source_site}).limit(count)
    else:
        list_mangas = tx_mangas.find({"source_site": source_site})
    if mode == 'update':
        list_mangas = list(tx_mangas.find(
            {"original_id": {"$in": list_update_original_id}}))
    for manga in list_mangas:
        # Check if manga in DB:
        # existed_manga_query = db.query(NewManga).where(NewManga.original_id == manga['original_id']).where(NewManga.status == 1)
        if type == 'manga' or type == 'all':
            logging.info('Inserting or update manga: %s' %
                         manga['original_id'])
            new_push_manga_to_db(db, manga, tx_manga_bucket_mapping, slug_format, publish)
            logging.info('Manga inserted or updated')
        if type == 'chapter' or type == 'all':
            existed_manga = db.query(NewManga).where(
                NewManga.original_id == manga['original_id']).first()
            if existed_manga is not None:
                bucket = tx_manga_bucket_mapping.find_one({'$or': [{"original_id": existed_manga.original_id}, {
                                                          "original_id": existed_manga.original_id.lower()}]})['bucket']
                chapters = manga['chapters']
                if not bulk:
                    for chapter in chapters:
                        chapter_dict = new_chapter_builder(
                            chapter, existed_manga.id, source_site=source_site, publish=publish)
                        new_push_chapter_to_db(
                            db, chapter_dict, bucket, existed_manga.id, existed_manga.slug, upload, tx_manga_errors)
                else:
                    list_chapter_dict = []
                    for chapter in chapters:
                        chapter_dict = new_chapter_builder(
                            chapter, existed_manga.id, source_site=source_site, publish=publish)
                        list_chapter_dict.append(chapter_dict)
                    new_push_chapter_to_db_bulk(db, list_chapter_dict, bucket, existed_manga.id, existed_manga.slug, upload, tx_manga_errors)
                        


def process_push_to_db(mode='crawl', type='manga', list_update_original_id=None, source_site=MangaSourceEnum.MANGASEE.value, upload=True, count=None, slug_format=False, publish=True, bulk=False):
    # Connect DB
    db = Connection().mysql_connect(db_name='mangamonster_com')
    mongo_client = Connection().mongo_connect()
    mongo_db = mongo_client['mangamonster']
    tx_manga_bucket_mapping = mongo_db['tx_manga_bucket_mapping']
    tx_mangas = mongo_db['tx_mangas']
    tx_manga_errors = mongo_db['tx_manga_errors']
    logging.info('Getting data with source site: %s' % source_site)
    if count:
        list_mangas = tx_mangas.find({"source_site": source_site}).limit(count)
    else:
        list_mangas = tx_mangas.find({"source_site": source_site})
    if mode == 'update':
        list_mangas = list(tx_mangas.find(
            {"original_id": {"$in": list_update_original_id}}))
    logging.info('==================== %s' % list_mangas)
    for manga in list_mangas:
        # Check if manga in DB:
        existed_manga_query = db.query(Manga).where(
            Manga.slug_original == manga['original_id'].lower()).where(Manga.status == 1)
        if type == 'manga' or type == 'all':
            if existed_manga_query.first() is None:
                logging.info('Inserting manga: %s' % manga['original_id'])
                
                logging.info('slug format prepare %s' % slug_format)
                push_manga_to_db(db, manga, slug_format, publish)
                
                process_insert_bucket_mapping(
                    manga['original_id'], tx_manga_bucket_mapping)
                logging.info('Manga inserted')
        if type == 'chapter' or type == 'all':
            logging.info('Inserting manga chapters for manga: %s' %
                         manga['original_id'])
            existed_manga = existed_manga_query.first()
            logging.info(existed_manga.slug)
            bucket = tx_manga_bucket_mapping.find_one({'$or': [{"original_id": existed_manga.slug_original}, {
                                                      "original_id": existed_manga.slug_original.lower()}]})['bucket']
            logging.info(bucket)
            if existed_manga is not None:
                chapters = manga['chapters']
                list_processed_chapter_dict = []
                for chapter in chapters:
                    # db_manga_chapter = db.query(MangaChapters).where(MangaChapters.manga_id == existed_manga.id).where(
                    #     MangaChapters.ordinal == chapter['ordinal']).where(MangaChapters.season == chapter['season']).where(MangaChapters.status == 1).first()
                    # if db_manga_chapter is None:
                    chapter_dict = chapter_builder(
                        chapter, existed_manga.id, publish=publish)
                    s3_prefix = 'storage/' + existed_manga.slug_original.lower() + '/' + \
                        chapter['season'] + '/' + chapter['chapter_number'] + \
                        '/' + chapter['chapter_part']
                    list_processed_chapter_dict.append({'chapter_dict': chapter_dict, 'pages': chapter['pages'], 'resources': chapter[
                                                        'resources'], 'resources_storage': chapter['resources_storage'], 's3_prefix': s3_prefix})
                logging.info('push chapter to db')
                # Insert to database
                for processed_chapter_dict in list_processed_chapter_dict:
                    push_chapter_to_db(db, processed_chapter_dict, bucket, existed_manga.id,
                                       insert=insert, upload=upload, error=tx_manga_errors)
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
