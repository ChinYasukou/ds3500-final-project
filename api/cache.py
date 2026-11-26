"""Bounded, thread-safe TTL cache for successful API responses."""

from copy import deepcopy
from threading import RLock
from time import monotonic

from api.storage import database_path


class ResponseCache:
    def __init__(self, ttl=300, max_entries=256, clock=monotonic):
        if ttl <= 0 or max_entries <= 0:
            raise ValueError("Cache TTL and capacity must be positive")
        self.ttl = ttl
        self.max_entries = max_entries
        self.clock = clock
        self.entries = {}
        self.lock = RLock()

    def get_or_compute(self, key, calculate):
        with self.lock:
            now = self.clock()
            entry = self.entries.get(key)
            if entry is not None and entry[0] > now:
                return deepcopy(entry[1])
            # A failed calculation never creates or replaces a cached response.
            result = calculate()
            expired = [key for key, (expires, _) in self.entries.items() if expires <= self.clock()]
            for expired_key in expired:
                del self.entries[expired_key]
            if len(self.entries) >= self.max_entries:
                oldest = min(self.entries, key=lambda key: self.entries[key][0])
                del self.entries[oldest]
            self.entries[key] = (self.clock() + self.ttl, deepcopy(result))
            return deepcopy(result)

    def clear(self):
        with self.lock:
            self.entries.clear()


def query_cache_key(endpoint: str, **parameters) -> tuple:
    """Call after validating/defaulting every parameter that affects the result."""
    return (str(database_path().resolve()), endpoint, tuple(sorted(parameters.items())))


response_cache = ResponseCache()
