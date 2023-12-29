from extractors.mangasee_extractor import MangaseeExtractor

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def process_manga(source_site, *args):
    if source_site == 'mangasee':
        MangaseeExtractor().extract_manga_info(source_site, *args)
