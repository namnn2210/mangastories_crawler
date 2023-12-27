from extractors.mangasee_extractor import MangaseeExtractor

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def process_manga(manga_url, source_site):
    if source_site == 'mangasee':
        MangaseeExtractor().extract_manga_info(manga_url, source_site)
