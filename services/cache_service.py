"""
In-memory cache service untuk CryptoTracker BMZ.
Menggunakan dictionary dengan TTL. Tidak memerlukan Redis.
"""
import time
import threading
from typing import Any, Optional


class CacheService:
    """Thread-safe in-memory cache dengan TTL."""

    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def _make_key(self, namespace: str, **kwargs) -> str:
        """Buat cache key dari namespace + kwargs."""
        parts = [namespace]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                parts.append(f"{k}={v}")
        return ":".join(parts)

    def get(self, namespace: str, **kwargs) -> Optional[Any]:
        """Ambil nilai dari cache. Returns None jika expired atau tidak ada."""
        key = self._make_key(namespace, **kwargs)
        with self._lock:
            if key not in self._store:
                return None
            expiry, value = self._store[key]
            if time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, namespace: str, value: Any, ttl: int, **kwargs) -> None:
        """Simpan nilai ke cache dengan TTL dalam detik."""
        key = self._make_key(namespace, **kwargs)
        with self._lock:
            self._store[key] = (time.time() + ttl, value)

    def invalidate(self, namespace: str, **kwargs) -> None:
        """Hapus satu entry dari cache."""
        key = self._make_key(namespace, **kwargs)
        with self._lock:
            self._store.pop(key, None)

    def clear(self, namespace: Optional[str] = None) -> None:
        """Hapus semua cache, atau hanya namespace tertentu."""
        with self._lock:
            if namespace is None:
                self._store.clear()
            else:
                self._store = {
                    k: v for k, v in self._store.items()
                    if not k.startswith(namespace + ":")
                }


# Singleton instance — digunakan di seluruh aplikasi
cache = CacheService()
