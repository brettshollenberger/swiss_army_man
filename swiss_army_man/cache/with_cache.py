import time
from functools import wraps
from inspect import signature
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
            # Fetch function's arguments
            sig = signature(func)
            func_args = {param.name: kwargs.get(param.name, param.default) if param.default is not param.empty else None
                         for param in sig.parameters.values()}
            
            # Determine required arguments for key_func by inspecting its signature
            key_func_signature = signature(key_func)
            key_args_needed = {name: func_args[name] for name in key_func_signature.parameters if name in func_args}

            # Determine the cache key using key_func with only the required arguments
            cache_key = key_func(**key_args_needed) if callable(key_func) else key_func

            current_time = time.time()
            entry = cache_store.get(cache_key) or {'timestamp': 0, 'value': None}

            # Calculate expiry if provided
            if expires_in is not None:
                expiry = DateUtils.parse_relative_date(expires_in, format="seconds")
            else:
                expiry = None

            # Check if force refreshing is needed or the entry is expired
            should_refresh = force or kwargs.get('force', False) or \
                             (entry['timestamp'] == 0) or \
                             (expiry is not None and (current_time - entry['timestamp'] > expiry))
            if should_refresh:
                result = func(*args, **kwargs)
                cache_store.set(cache_key, {'timestamp': current_time, 'value': result})
                return result

            return cache_store.get(cache_key)['value']

        return wrapper
    return decorator
