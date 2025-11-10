
from __future__ import annotations
import time
import threading
from typing import Any, Dict, Tuple, Optional

class SWRCache:
    def __init__(self):
        self._store: Dict[str, Tuple[float, int, Any]] = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: Any, ttl: int = 900) -> None:
        with self._lock:
            self._store[key] = (time.time(), ttl, value)

    def get(self, key: str) -> Tuple[Optional[Any], bool]:
        
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None, False
            ts, ttl, val = item
            fresh = (time.time() - ts) < ttl
            return val, fresh

    def get_if_exists(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._store.get(key)
            return None if not item else item[2]

swr_cache = SWRCache()

__all__ = ["swr_cache"]
