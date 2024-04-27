from functools import wraps
from .redis_cache import RedisCache

CACHES = {
    "redis": RedisCache
}
def cache(key_func, force=False, cache_type="redis"):
    cache_store = CACHES[cache_type]()
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Determine the cache key based on the type of key_func
            if callable(key_func):
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = key_func

            # Check if force refreshing is needed
            if force or kwargs.get('force', False):
                result = func(*args, **kwargs)
                cache_store.set(cache_key, result)
                return result

            # Retrieve from cache or call the function
            if cache_key not in cache_store:
                result = func(*args, **kwargs)
                cache_store.set(cache_key, result)
            return cache_store.get(cache_key)
        return wrapper
    return decorator