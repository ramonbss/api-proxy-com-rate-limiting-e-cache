from typing import Any

from cachetools import TTLCache

from app.core.interfaces import ICacheService


class TTLCacheService(ICacheService):
    """
    Cache in-memory com TTL (Time-To-Live) e LRU (Least Recently Used).

    TTL:  cada item expira automaticamente após `default_ttl` segundos.
    LRU:  quando `max_size` é atingido, o item menos recentemente acessado é descartado.
    """

    def __init__(self, max_size: int = 512, default_ttl: int = 60) -> None:
        self._cache: TTLCache = TTLCache(maxsize=max_size, ttl=default_ttl)
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._cache[key] = value

    async def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    async def clear(self) -> None:
        self._cache.clear()
