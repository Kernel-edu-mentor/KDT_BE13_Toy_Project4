# paper_qa/utils/cache.py
from functools import lru_cache
from typing import List

class QueryCache:
    def __init__(self, maxsize=100):
        self.cache = {}
        self.maxsize = maxsize

    def get(self, key: str):
        return self.cache.get(key)

    def set(self, key: str, value):
        if len(self.cache) >= self.maxsize:
            # FIFO 제거
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = value

query_cache = QueryCache()