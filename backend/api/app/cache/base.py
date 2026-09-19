"""
Cache abstraction (spek poin 35 - CACHING).

`InMemoryCache` dipakai untuk dev/test di sandbox ini (tidak butuh Redis).
Di production, ganti dengan `RedisCache` (implementasi kompatibel interface
yang sama) tanpa mengubah call-site -- contoh kerangka Redis disertakan
di bagian bawah file, tidak dijalankan di sini karena `redis` package
tidak terpasang & tidak ada network untuk connect ke Redis server.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


class Cache(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...


@dataclass
class _Entry:
    value: Any
    expires_at: float


class InMemoryCache(Cache):
    """Cache in-process sederhana dengan TTL. Thread-unsafe secara sengaja
    (single-process dev use) -- untuk multi-worker production pakai Redis."""

    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        self._store[key] = _Entry(
            value=value, expires_at=time.monotonic() + ttl_seconds
        )

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def __len__(self) -> int:
        return len(self._store)


# TTL yang disarankan per jenis data (detik) -- lihat spek poin 35.
# Angka ini adalah starting point, sesuaikan dengan rate-limit provider asli.
RECOMMENDED_TTL_SECONDS: dict[str, float] = {
    "ohlcv:1m": 15,
    "ohlcv:5m": 30,
    "ohlcv:15m": 60,
    "ohlcv:1H": 120,
    "ohlcv:4H": 300,
    "ohlcv:1D": 900,
    "ticker": 5,
    "indicators": 30,
    "news": 300,
    "economic_calendar": 3600,
    "order_book": 2,
    "ai_analysis": 60,
}


class RedisCache(Cache):  # pragma: no cover - kerangka, tidak dites di sandbox
    """
    Kerangka implementasi Redis. TIDAK dijalankan/dites di sandbox ini
    (package `redis` tidak terpasang, tidak ada network). Ditulis lengkap
    supaya bisa langsung dipakai saat deploy ke environment nyata.
    """

    def __init__(self, redis_client: Any) -> None:
        self._client = redis_client

    def get(self, key: str) -> Optional[Any]:
        import json

        raw = self._client.get(key)
        return json.loads(raw) if raw is not None else None

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        import json

        self._client.set(key, json.dumps(value), ex=int(ttl_seconds))

    def delete(self, key: str) -> None:
        self._client.delete(key)

