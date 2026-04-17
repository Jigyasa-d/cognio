cache = {}

def set_cache(key, value):
    cache[key] = value

def get_cache(key):
    return cache.get(key)