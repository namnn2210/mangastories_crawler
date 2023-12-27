import redis


class RedisCache(object):

    def __init__(self, db=0):
        self.pool = redis.ConnectionPool(
            host='localhost', port=6379, db=db)

    def get_redis(self):
        return redis.StrictRedis(connection_pool=self.pool)

    def keys(self, pattern='*'):
        rd = self.get_redis()
        return rd.keys(pattern)

    def get(self, key):
        rd = self.get_redis()
        return rd.get(key)

    def hget(self, name, key):
        rd = self.get_redis()
        return rd.hget(name, key)

    def getlistkeybyprefix(self, prefix_key):
        rd = self.get_redis()
        return rd.scan_iter(prefix_key+":*")

    # expired = seconds
    def set(self, key, value, expires=None):
        rd = self.get_redis()
        rd.set(key, value, ex=expires)

    def hset(self, name, key, value):
        rd = self.get_redis()
        rd.hset(name, key, value)

    def append(self, key, value, expires=None):
        rd = self.get_redis()
        if not rd.exists(key):
            self.set(key, value, expires)
        else:
            value_exist = rd.get(key)
            s = set()
            if value_exist:
                s = s.union(set(value_exist.split(",")))
            if value:
                s = s.union(set(value.split(",")))
            self.set(key, ",".join(s), expires)

    def delete(self, key):
        rd = self.get_redis()
        rd.delete(key)

    def sadd(self, queue_name, value):
        rd = self.get_redis()
        rd.sadd(queue_name, value)

    def put_to_priority(self, queue_name, value, level_priority):
        rd = self.get_redis()
        rd.zincrby(queue_name, value, level_priority)
