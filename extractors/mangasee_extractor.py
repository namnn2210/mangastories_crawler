from .base.extractor import Extractor


class MangaseeExtractor(Extractor):

    def extract_manga_info(self, manga_url, source_site):
        print(manga_url, source_site)

    def extract_chapter_info(self, chapter_url, source_site, manga_original_id):
        print(chapter_url, source_site, manga_original_id)
