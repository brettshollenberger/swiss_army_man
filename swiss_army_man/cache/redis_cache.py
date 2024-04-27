import pickle
import redis
import os
import json
import yaml
from typing import Callable
from .. import project_root
from tqdm import tqdm

class RedisCache:
    def __init__(self, conf=None):
        if conf is not None:
            self.CONFIG = conf
        else:
            # Pass these into the Docker container using the docker-compose.yml file and the .env file
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = os.getenv('REDIS_PORT', 6379)
            self.CONFIG = { 'REDIS_HOST': redis_host, 'REDIS_PORT': redis_port, 'REDIS_DB': 0 }

        self.REDIS_POOL = redis.ConnectionPool(
            host=self.CONFIG['REDIS_HOST'], port=self.CONFIG['REDIS_PORT'], db=self.CONFIG['REDIS_DB'])

        self.REDIS = redis.Redis(connection_pool=self.REDIS_POOL)

    def clear(self, redis_prefix: str):
        """
        Clear all keys with the given redis_prefix.
        """
        # Iterate through all the keys that match the prefix
        for key in self.REDIS.scan_iter(f"{redis_prefix}:*"):
            # Delete each matching key
            self.REDIS.delete(key)

    def get(self, key):
        raw_value = self.REDIS.get(key)
        return None if raw_value is None else pickle.loads(raw_value)

    def set(self, key, value):
        value = pickle.dumps(value)
        self.REDIS.set(key, value)

    def lpush(self, key, value):
        return self.REDIS.lpush(key, value)

    def get_redis_key(self, raw_value: str, redis_prefix: str) -> str:
        return f'{redis_prefix}:{raw_value.lower().replace(" ", "_")}'

    def fetch_from_redis(self, keys: list, redis_prefix: str):
        redis_keys = [self.get_redis_key(key, redis_prefix) for key in keys]
        results = self.REDIS.mget(redis_keys)
        data = {key: pickle.loads(item) for key, item in zip(
            keys, results) if item is not None}
        missing_data = [key for key, item in zip(
            keys, results) if item is None]
        return data, missing_data

    def store_in_redis(self, data_dict: dict, redis_prefix: str):
        serialized_data = {self.get_redis_key(key, redis_prefix): pickle.dumps(
            value) for key, value in data_dict.items()}
        self.REDIS.mset(serialized_data)

    # keys: list of keys to fetch
    # redis_prefix: prefix to use for redis keys
    # generate: how to generate
    def fetch_or_generate(self, keys: list, redis_prefix: str, computation: Callable) -> dict:
        data, missing_data_keys = self.fetch_from_redis(keys, redis_prefix)

        computed = {}
        if missing_data_keys:
            vals = [val.replace(redis_prefix + ":", "")
                    for val in missing_data_keys]
            key_vals = zip(missing_data_keys, vals)

            if len(missing_data_keys) > 1:
                gen = tqdm(key_vals, desc="Computation Progress",
                           total=len(missing_data_keys))
            else:
                gen = key_vals
            for k, v in gen:
                value = computation(v)
                self.store_in_redis({k: value}, redis_prefix)
                computed[k] = value

        data.update(computed)
        return data

    def count_keys(self, redis_prefix: str):
        return sum(1 for _ in self.REDIS.scan_iter(f"{redis_prefix}:*"))

    def dump_keys_to_file(self, redis_prefix: str, file_path: str):
        # Assuming you have a count method
        total_keys = self.count_keys(redis_prefix)
        with open(file_path, 'w') as f:
            for key in tqdm(self.REDIS.scan_iter(f"{redis_prefix}:*"), total=total_keys, desc="Dumping to file"):
                value = self.REDIS.get(key)
                value_str = pickle.loads(value)
                key_str = key.decode('utf-8').replace(f"{redis_prefix}:", "")
                f.write(f"{key_str}||{value_str}\n")

    def load_keys_from_file(self, file_path: str, redis_prefix: str):
        with open(file_path, 'r') as f:
            lines = f.readlines()
            pbar = tqdm(lines, desc="Loading from file")
            for line in pbar:
                email, value_str = line.strip().split('||')
                redis_key = self.get_redis_key(email, redis_prefix)
                value = pickle.dumps(value_str)
                self.REDIS.set(redis_key, value)
