import time
from functools import wraps
from .redis_cache import RedisCache
from swiss_army_man.utils import DateUtils

CACHES = {
    "redis": RedisCache
}
def with_cache(key_func, force=False, cache_type="redis", expires_in=None):
    cache_store = CACHES[cache_type]()
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Determine the cache key based on the type of key_func
            if callable(key_func):
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = key_func

            current_time = time.time()
            entry = cache_store.get(cache_key) or {'timestamp': 0, 'value': None}
            if expires_in is None:
                expiry = None
            else:
                expiry = DateUtils.parse_relative_date(expires_in, format="seconds")

            # Check if force refreshing is needed
            if force or (entry['timestamp'] == 0) or (expiry is not None and (current_time - entry['timestamp'] > expiry)):
                result = func(*args, **kwargs)
                cache_store.set(cache_key, {'timestamp': current_time, 'value': result})
                return result

            return cache_store.get(cache_key)['value']
        return wrapper
    return decorator