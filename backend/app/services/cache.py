"""
Service: CacheService
Redis-Wrapper für schnelles Kurs-Caching und Rate-Limiting.
"""
from __future__ import annotations

import json
from typing import Optional, Any
from datetime import datetime

import redis.asyncio as aioredis

from app.core.config import get_settings


class CacheService:
    """
    Async Redis-Client für das Caching von Marktdaten.

    Verwendung:
        cache = CacheService()
        await cache.set_price("NVDA", {"price": 879.50, ...})
        data = await cache.get_price("NVDA")
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._client: Optional[aioredis.Redis] = None
        self._url = settings.redis_url
        self._default_ttl = settings.cache_ttl_seconds

    async def connect(self) -> None:
        self._client = aioredis.from_url(self._url, decode_responses=True)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()

    # ── Kurs-Cache ────────────────────────────────────────

    async def set_price(self, symbol: str, data: dict, ttl: int = 30) -> None:
        """Speichert Preisdaten für ein Symbol."""
        if not self._client:
            return
        key = f"price:{symbol.upper()}"
        data["cached_at"] = datetime.utcnow().isoformat()
        await self._client.setex(key, ttl, json.dumps(data))

    async def get_price(self, symbol: str) -> Optional[dict]:
        """Liest gecachte Preisdaten. None wenn nicht im Cache."""
        if not self._client:
            return None
        key = f"price:{symbol.upper()}"
        raw = await self._client.get(key)
        return json.loads(raw) if raw else None

    # ── Generisches Caching ───────────────────────────────

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self._client:
            return
        ttl = ttl or self._default_ttl
        await self._client.setex(key, ttl, json.dumps(value, default=str))

    async def get(self, key: str) -> Optional[Any]:
        if not self._client:
            return None
        raw = await self._client.get(key)
        return json.loads(raw) if raw else None

    async def delete(self, key: str) -> None:
        if self._client:
            await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        if not self._client:
            return False
        return bool(await self._client.exists(key))

    async def health(self) -> bool:
        """Gibt True zurück wenn Redis erreichbar ist."""
        try:
            if self._client:
                return await self._client.ping()
        except Exception:
            pass
        return False


# Singleton
_cache_service: Optional[CacheService] = None


def get_cache() -> CacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
