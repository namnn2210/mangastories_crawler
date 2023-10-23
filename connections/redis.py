from rq import Queue
from .redis_cache import RedisCache


def redis_connect(db=2, queue_name=''):
    redis_cache = RedisCache(db=db)
    return Queue(queue_name, connection=redis_cache.get_redis(), default_timeout=3600)
