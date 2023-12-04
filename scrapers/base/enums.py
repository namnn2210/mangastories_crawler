from enum import Enum, auto


class MangaMonsterBucketEnum(Enum):
    MANGAMONSTER = 'mangamonster'
    MANGAMONSTER1 = 'mangamonster1'
    MANGAMONSTER2 = 'mangamonster2'
    MANGAMONSTER4 = 'mangamonster4'
    MANGAMONSTER5 = 'mangamonster5'
    MANGAMONSTER8 = 'mangamonster8'
    MANGAMONSTER9 = 'mangamonster9'
    MANGAMONSTER10 = 'mangamonster10'
    MANGAMONSTER11 = 'mangamonster11'
    MANGAMONSTER12 = 'mangamonster12'
    MANGAMONSTER13 = 'mangamonster13-1'
    MANGAMONSTER15 = 'mangamonster15-1'
    MANGAMONSTER20 = 'mangamonster20'
    MANGAMONSTER21 = 'mangamonster21'
    MANGAMONSTER22 = 'mangamonster22'
    MANGAMONSTER26 = 'mangamonster26'
    MANGAMONSTER28 = 'mangamonster28'
    MANGAMONSTER29 = 'mangamonster29'
    MANGAMONSTER32 = 'mangamonster32'
    MANGAMONSTER33 = 'mangamonster33'


class MangaSourceEnum(Enum):
    MANGASEE = 'mangasee'
    MANHUAUS = 'manhuaus'
    ASURATOON = 'asuratoon'
    MANHUAPLUS = 'manhuaplus'
    MANGAREADER = 'mangareader'
    FLAMECOMICS = 'flamecomics'
    MANGAKAKALOT = 'mangakakalot'


class ErrorCategoryEnum(Enum):
    S3_UPLOAD = auto()
    MANGA_PROCESSING = auto()
