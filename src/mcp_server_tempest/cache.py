"""Disk cache for station data.

Persists station metadata to JSON files so it survives server restarts.
Each API token gets its own subdirectory (keyed by a truncated SHA-256 hash)
to isolate data between accounts.
"""

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import TypeVar

from platformdirs import user_cache_dir
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

DISK_CACHE_TTL_DEFAULT = 86400  # 24 hours


def _token_hash(token: str) -> str:
    """Return a truncated SHA-256 hex digest of the token."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]


class DiskCache:
    """JSON-file-based disk cache for Pydantic models, scoped per API token."""

    def __init__(self, token: str, ttl: int | None = None) -> None:
        self.ttl = (
            ttl
            if ttl is not None
            else int(os.getenv("WEATHERFLOW_DISK_CACHE_TTL", DISK_CACHE_TTL_DEFAULT))
        )
        self.cache_dir = Path(user_cache_dir("mcp-server-tempest")) / _token_hash(token)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_").replace("..", "_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str, model_class: type[T]) -> T | None:
        """Read a cached entry, returning None on miss, expiry, or error."""
        path = self._path(key)
        try:
            raw = json.loads(path.read_text())
            if time.time() - raw["timestamp"] > self.ttl:
                path.unlink(missing_ok=True)
                return None
            return model_class(**raw["data"])
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.warning("Disk cache read error for %s: %s", key, e)
            return None

    def set(self, key: str, model: BaseModel) -> None:
        """Write a model to disk cache."""
        path = self._path(key)
        try:
            payload = {"timestamp": time.time(), "data": model.model_dump(mode="json")}
            path.write_text(json.dumps(payload))
        except Exception:
            logger.warning("Disk cache write error for %s", key, exc_info=True)

    def clear(self) -> None:
        """Remove all cached files for this token."""
        try:
            for path in self.cache_dir.iterdir():
                if path.suffix == ".json":
                    path.unlink(missing_ok=True)
        except Exception:
            logger.warning("Disk cache clear error", exc_info=True)
