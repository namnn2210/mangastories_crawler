from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, SMALLINT, Text, BIGINT, Float, Double
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime

Base = declarative_base()


class Manga(Base):
    __tablename__ = "tx_mangas"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    idx = Column(String(36))
    name = Column(String(255))
    slug = Column(String(255))
    thumb = Column(String(255))
    description = Column(Text)
    rate = Column(Float)
    original = Column(String(255))
    featured = Column(SMALLINT, default=0)
    type = Column(SMALLINT, default=1)
    ordinal = Column(SMALLINT, default=0)
    chapters = Column(String(255))
    published = Column(DateTime, default=datetime.now())
    finished = Column(SMALLINT, default=0)
    status = Column(SMALLINT, default=1)
    manga_author_ids = Column(String(255))
    manga_genre_ids = Column(String(255))
    manga_type_id = Column(SMALLINT, default=1)
    meta_tag_id = Column(BIGINT)
    created_by = Column(BIGINT, default=1)
    updated_by = Column(BIGINT, default=1)
    deleted_by = Column(BIGINT)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    total_view = Column(Integer)
    author = Column(String(255))
    genre = Column(String(255))
    official_translation = Column(String(100))
    rss = Column(String(50))
    weblink = Column(SMALLINT, default=0)
    local_url = Column(String(255))
    search_text = Column(Text)
    search_field = Column(Text)
    slug_original = Column(String(255))


class MangaChapters(Base):
    __tablename__ = "tx_manga_chapters"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    idx = Column(String(36))
    name = Column(String(255))
    slug = Column(String(255))
    thumb = Column(String(255))
    description = Column(Text)
    original = Column(String(255))
    ordinal = Column(Float, default=0)
    season = Column(Integer)
    published = Column(DateTime, default=datetime.now())
    status = Column(SMALLINT, default=1)
    manga_id = Column(String(255))
    meta_tag_id = Column(BIGINT)
    resource_status = Column(String(255))
    created_by = Column(BIGINT, default=1)
    updated_by = Column(BIGINT, default=1)
    deleted_by = Column(BIGINT)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    total_view = Column(Integer)
    new_slug = Column(String(255))
    chapter_source = Column(String(255))


class MangaSource(Base):
    __tablename__ = "tx_manga_sources"
    
    id = Column(Integer, primary_key=True, autoincrement="auto")
    idx = Column(String(36))
    name = Column(String(255))
    slug = Column(String(255))
    status = Column(SMALLINT, default=1)
    created_by = Column(BIGINT, default=1)
    updated_by = Column(BIGINT, default=1)
    deleted_by = Column(BIGINT)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    
class MangaSourceRelations(Base):
    __tablename__ = "tx_manga_source_relations"
    
    id = Column(Integer, primary_key=True, autoincrement="auto")
    manga_id = Column(BIGINT)
    source_id = Column(BIGINT)
    ordinal = Column(Float, default=0)
    status = Column(SMALLINT, default=1)
    created_by = Column(BIGINT, default=1)
    deleted_by = Column(BIGINT)
    created_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    
    
class MangaChapterResources(Base):
    __tablename__ = "tx_manga_chapter_resources"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    idx = Column(String(36))
    name = Column(String(255))
    slug = Column(String(255))
    thumb = Column(String(255))
    storage = Column(String(255))
    original = Column(String(255))
    type = Column(SMALLINT, default=0)
    ordinal = Column(SMALLINT, default=0)
    status = Column(SMALLINT, default=1)
    manga_chapter_id = Column(String(255))
    created_by = Column(Integer, default=1)
    updated_by = Column(Integer, default=1)
    deleted_by = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    chapter_source = Column(String(255))
    
    
class NewManga(Base):
    __tablename__ = "tx_mangas"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    idx = Column(String(36))
    mal_id = Column(String(36))
    name = Column(String(255))
    alt_name = Column(String(255))
    slug = Column(String(255))
    thumb = Column(String(255))
    cover = Column(String(255))
    description = Column(Text)
    original = Column(String(255))
    original_id = Column(String(255))
    featured = Column(SMALLINT, default=0)
    type = Column(SMALLINT, default=1)
    ordinal = Column(SMALLINT, default=0)
    published = Column(DateTime, default=datetime.now())
    publish_status = Column(DateTime, default=datetime.now())
    finished = Column(SMALLINT, default=0)
    latest_chapter_published= Column(DateTime, default=datetime.now())
    status = Column(SMALLINT, default=1)
    popularity = Column(Integer)
    rank = Column(Integer)
    score = Column(Double)
    num_scoring_users = Column(Integer)
    num_list_users = Column(Integer)
    num_chapters = Column(Integer)
    num_volumes = Column(Integer)
    total_view = Column(Integer)
    manga_authors = Column(String(255))
    manga_genres = Column(String(255))
    manga_type_id = Column(SMALLINT, default=1)
    meta_tag_id = Column(BIGINT)
    created_by = Column(BIGINT, default=1)
    updated_by = Column(BIGINT, default=1)
    deleted_by = Column(BIGINT)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    official_translation = Column(String(100))

class NewMangaChapters(Base):
    __tablename__ = "tx_manga_chapters"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    idx = Column(String(36))
    name = Column(String(255))
    alt_name = Column(String(255))
    slug = Column(String(255))
    thumb = Column(String(255))
    description = Column(Text)
    original = Column(String(255))
    original_id = Column(String(255))
    ordinal = Column(SMALLINT, default=0)
    chapter_no = Column(Integer)
    chapter_part = Column(SMALLINT, default=0)
    season = Column(SMALLINT, default=0)
    chapter_code = Column(String(255))
    resources =  Column(LONGTEXT)
    resource_storage = Column(String(255))
    resource_total = Column(Integer)
    resource_download = Column(SMALLINT, default=0)
    resource_bucket = Column(String(255))
    type = Column(String(255))
    
        
    published = Column(DateTime, default=datetime.now())
    status = Column(SMALLINT, default=1)

    total_view = Column(Integer)
    manga_id = Column(Integer)

    created_by = Column(BIGINT, default=1)
    updated_by = Column(BIGINT, default=1)
    deleted_by = Column(BIGINT)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    official_translation = Column(String(100))