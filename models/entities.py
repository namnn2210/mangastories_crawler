from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, SMALLINT, Text, BIGINT, Float
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
    deleted_by = Column(BIGINT, default=1)
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
    deleted_by = Column(BIGINT, default=1)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now())
    deleted_at = Column(DateTime)
    total_view = Column(Integer)
    new_slug = Column(String(255))
    chapter_source = Column(String(255))
