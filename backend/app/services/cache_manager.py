import hashlib
import os
import time

cache_store = {}
TTL = 60 * 60 * 24


def should_disable_cache() -> bool:
    return os.getenv("DEMO_DISABLE_CACHE", "0") == "1"


def _signature(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def generate_cache_key(content_id: str, strain_level: str, behavior_summary: str = ""):
    behavior_part = _signature(behavior_summary.strip()) if behavior_summary else "generic"
    return f"{content_id}:{strain_level}:{behavior_part}"


def get_from_cache(key: str):
    if should_disable_cache():
        return None

    entry = cache_store.get(key)
    if not entry:
        return None

    if time.time() > entry["expiry"]:
        del cache_store[key]
        return None

    return entry["value"]


def set_cache(key: str, value: str):
    if should_disable_cache():
        return

    cache_store[key] = {
        "value": value,
        "expiry": time.time() + TTL
    }