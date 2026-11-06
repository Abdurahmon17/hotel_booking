# hotel_booking/api_cache.py
"""The cache for the free-room search (P08): cache-aside in Redis, with a TTL and a version.

PostgreSQL is the source of truth. Redis keeps copies of search answers for 30 seconds.
Booking and cancelling never read the cache.
"""
from __future__ import annotations

from typing import Protocol

from redis import Redis

TTL_SECONDS = 30
VERSION_KEY = "availability:version"


class KeyValueStore(Protocol):
    """The three Redis commands the cache uses: GET, SET with a time to live, and INCR."""

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ttl_seconds: int) -> None: ...
    def increment(self, key: str) -> None: ...


class RedisKeyValueStore:
    """The three commands, sent to Redis."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def get(self, key: str) -> str | None:
        return self._redis.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._redis.set(key, value, ex=ttl_seconds)

    def increment(self, key: str) -> None:
        self._redis.incr(key)


class AvailabilityCache:
    """Copies of search answers: the free room numbers for one stay, such as "R7,R8"."""

    def __init__(self, store: KeyValueStore) -> None:
        self._store = store

    def key(self, check_in: str, check_out: str) -> str:
        # The version is part of the key, so raising it makes every older copy unreachable.
        version = self._store.get(VERSION_KEY) or "0"
        return f"availability:v{version}:{check_in}:{check_out}"

    def get(self, key: str) -> str | None:
        return self._store.get(key)

    def set(self, key: str, room_numbers: str) -> None:
        self._store.set(key, room_numbers, TTL_SECONDS)

    def invalidate(self) -> None:
        """A booking or a cancellation changed what is free: every cached search is now out of date."""
        self._store.increment(VERSION_KEY)