import pickle
import redis
import os
import json
import yaml
from typing import Callable
from .. import project_root
from tqdm import tqdm

class RedisCache:
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
        with self.REDIS.client() as client:
            return client.delete(key)

    def get(self, key):
        with self.REDIS.client() as client:
            raw_value = client.get(key)
            return None if raw_value is None else pickle.loads(raw_value)

    def set(self, key, value):
        with self.REDIS.client() as client:
            value = pickle.dumps(value)
            return client.set(key, value)

    def lpush(self, key, value):
        with self.REDIS.client() as client:
            return client.lpush(key, value)