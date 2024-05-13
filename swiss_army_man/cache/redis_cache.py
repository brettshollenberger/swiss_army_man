import pickle
import redis
import os
import json
import yaml
from typing import Callable
from swiss_army_man.utils import project_root, Singleton
from tqdm import tqdm

# Because we use the Singleton pattern here, the connection pool will be shared
# across the entire app everywhere it's imported. Due to this, you may want to initialize
# it on app creation in order to pass your preferred configuration in a single place.
class RedisCache(Singleton):
    def __init__(self, config={}):
        default_config = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": os.getenv("REDIS_PORT", 6379),
            "db": 0,
            "max_connections": 30,
        }
        self.CONFIG = {
            **default_config,
            **config
        }

        self.REDIS_POOL = redis.ConnectionPool(**self.CONFIG)
        self.REDIS = redis.Redis(connection_pool=self.REDIS_POOL)

    def clear(self, redis_prefix: str):
        """
        Clear all keys with the given redis_prefix.
        """
        # Iterate through all the keys that match the prefix
        for key in self.REDIS.scan_iter(f"{redis_prefix}:*"):
            # Delete each matching key
            self.REDIS.delete(key)

    def delete(self, key):
        return self.REDIS.delete(key)

    def get(self, key):
        raw_value = self.REDIS.get(key)
        return None if raw_value is None else pickle.loads(raw_value)

    def set(self, key, value):
        value = pickle.dumps(value)
        return self.REDIS.set(key, value)

    def lpush(self, key, value):
        return self.REDIS.lpush(key, value)