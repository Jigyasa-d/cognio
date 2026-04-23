import time

cache_store = {}

TTL = 60 * 60 * 24 * 7  # 7 days


def generate_cache_key(content_id: str, strain_level: str):
    return f"{content_id}:{strain_level}"


def get_from_cache(key: str):
    entry = cache_store.get(key)

    if not entry:
        return None

    if time.time() > entry["expiry"]:
        del cache_store[key]
        return None

    return entry["value"]


def set_cache(key: str, value: str):
    cache_store[key] = {
        "value": value,
        "expiry": time.time() + TTL
    }