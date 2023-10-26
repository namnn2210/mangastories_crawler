from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from PIL import ImageFile, Image
from configs.config import WEBP_QUALITY
from hashids import Hashids
from io import BytesIO


import requests
import json
import io
import logging


ImageFile.LOAD_TRUNCATED_IMAGES = True
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def get_soup(url, header):
    return BeautifulSoup(urlopen(Request(url=url, headers=header)), 'html.parser')

def save_to_json(file_name,json_dict):
    with open(f'json/{file_name}','r') as json_file:
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


def image_s3_upload(s3, root_directory, image_url, manga_no, formatted_img_count, slug, season, bucket):
    # s3 = s3_connect()
    img = watermark_with_transparency_io(
        BytesIO(requests.get(image_url).content), 'watermark/new_watermark.png')
    # resized_image = resize_img(img)
    img_name = '{}.webp'.format(formatted_img_count)
    manga_ordinal = format_leading_chapter(int(float(manga_no)))
    season_path = format_leading_part(int(season))
    manga_part = format_leading_part(int(float(manga_no) % 1 * 10))
    img_src = '{}/{}/{}/{}/{}/{}'.format(root_directory, slug.lower(),
                                         season_path, manga_ordinal, manga_part, img_name)
    logging.info(img_src)
    s3.put_object(Bucket=bucket, Key=img_src, Body=img,
                  ACL='public-read', ContentType='image/webp')
