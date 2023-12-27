import logging


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def process_manga(manga_url, source_site):
    if source_site == 'mangasee':
       print(manga_url)
