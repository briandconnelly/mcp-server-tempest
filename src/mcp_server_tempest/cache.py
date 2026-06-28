"""Disk cache for station data.

Persists station metadata to JSON files so it survives server restarts.
Each API token gets its own subdirectory (keyed by a truncated SHA-256 hash)
to isolate data between accounts.

Cached payloads include precise station coordinates and Wi-Fi SSIDs, so on a
multi-user host the directory and files are created with owner-only permissions
(0700/0600) and writes are atomic. The token-hash directory name is
naming-isolation, not access control. POSIX modes do not map to Windows ACLs,
so the permission hardening is a POSIX-only best-effort (see _secure_dir).
"""

import hashlib
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import TypeVar

from platformdirs import user_cache_dir
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

DISK_CACHE_TTL_DEFAULT = 86400  # 24 hours

_DIR_MODE = 0o700
_FILE_MODE = 0o600


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
        self.cache_dir.mkdir(parents=True, exist_ok=True, mode=_DIR_MODE)
        self._secure_dir()

    def _secure_dir(self) -> None:
        """Tighten permissions on the cache dir and any pre-existing entries.

        mkdir's mode is masked by the process umask, and directories/files left
        by older versions may be world-readable, so we chmod explicitly. This
        also migrates pre-existing installs in place rather than discarding the
        cache. On platforms where POSIX modes don't map to ACLs (e.g. Windows)
        chmod is a harmless best-effort.

        If the cache dir is itself a symlink we refuse to operate on it: chmod
        would follow the link and re-mode its target, and iterating it would
        traverse outside the intended location. Planting that symlink requires
        write access to the user's own cache dir (same-user compromise), which
        is outside this fix's threat model (confidentiality from *other* local
        users), but bailing is cheap defense-in-depth.
        """
        if self.cache_dir.is_symlink():
            logger.warning(
                "Cache dir %s is a symlink; skipping permission hardening", self.cache_dir
            )
            return
        try:
            os.chmod(self.cache_dir, _DIR_MODE)
            for entry in self.cache_dir.iterdir():
                # Only touch real files we own; never follow a symlink.
                if entry.is_file() and not entry.is_symlink():
                    os.chmod(entry, _FILE_MODE)
        except OSError as e:
            logger.warning("Could not secure cache dir %s: %s", self.cache_dir, e)

    def _path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_").replace("..", "_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str, model_class: type[T]) -> T | None:
        """Read a cached entry, returning None on miss, expiry, or error."""
        hit = self.get_with_age(key, model_class)
        return hit[0] if hit is not None else None

    def get_with_age(self, key: str, model_class: type[T]) -> tuple[T, float] | None:
        """Read a cached entry with its stored write timestamp (epoch seconds).

        Returns the (model, timestamp) pair, or None on miss, expiry, or error.
        The timestamp populates _meta.ts_retrieved so an agent can judge the
        freshness of a disk-cached response.
        """
        path = self._path(key)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            ts = raw["timestamp"]
            if time.time() - ts > self.ttl:
                path.unlink(missing_ok=True)
                return None
            return model_class(**raw["data"]), float(ts)
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.warning("Disk cache read error for %s: %s", key, e)
            return None

    def set(self, key: str, model: BaseModel) -> None:
        """Write a model to disk cache atomically with owner-only permissions.

        The payload is written to a uniquely-named temp file in the same
        directory (mkstemp creates it 0600 regardless of umask, with O_EXCL),
        then os.replace()'d onto the final path. os.replace is atomic within a
        directory and preserves the temp file's mode, so a reader never sees a
        partial or world-readable file. Durability is process-crash safe, not
        power-loss durable — acceptable for a regenerable cache.
        """
        path = self._path(key)
        tmp_name: str | None = None
        try:
            payload = {"timestamp": time.time(), "data": model.model_dump(mode="json")}
            tmp_fd, tmp_name = tempfile.mkstemp(
                dir=self.cache_dir, prefix=f".{path.name}.", suffix=".tmp"
            )
            # Pin UTF-8 so writes/reads agree regardless of the host locale.
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.replace(tmp_name, path)
        except Exception:
            # Caching is best-effort: a full/read-only/unavailable cache must
            # never fail an otherwise-successful tool call, it just skips
            # persistence. Clean up any temp artifact left behind.
            logger.warning("Disk cache write error for %s", key, exc_info=True)
            if tmp_name is not None:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass

    def clear(self) -> None:
        """Remove all cached files (and any stray temp files) for this token."""
        try:
            for path in self.cache_dir.iterdir():
                if path.suffix in (".json", ".tmp"):
                    path.unlink(missing_ok=True)
        except Exception:
            logger.warning("Disk cache clear error", exc_info=True)
