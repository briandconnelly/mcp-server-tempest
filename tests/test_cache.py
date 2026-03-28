"""Tests for the disk cache module."""

import json
import time

import pytest
from pydantic import BaseModel

from mcp_server_tempest.cache import DiskCache, _token_hash


class SampleModel(BaseModel):
    name: str
    value: int


@pytest.fixture()
def disk_cache(tmp_path, monkeypatch):
    """Create a DiskCache that writes to a temp directory."""
    monkeypatch.setattr(
        "mcp_server_tempest.cache.user_cache_dir",
        lambda app_name: str(tmp_path),
    )
    return DiskCache(token="test-token", ttl=3600)


class TestTokenHash:
    def test_deterministic(self):
        assert _token_hash("abc") == _token_hash("abc")

    def test_different_tokens_differ(self):
        assert _token_hash("token-a") != _token_hash("token-b")

    def test_length(self):
        assert len(_token_hash("any-token")) == 16


class TestDiskCache:
    def test_set_and_get(self, disk_cache):
        model = SampleModel(name="test", value=42)
        disk_cache.set("key1", model)
        result = disk_cache.get("key1", SampleModel)
        assert result is not None
        assert result.name == "test"
        assert result.value == 42

    def test_get_missing_key(self, disk_cache):
        assert disk_cache.get("nonexistent", SampleModel) is None

    def test_expired_entry(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        dc = DiskCache(token="test-token", ttl=1)
        model = SampleModel(name="old", value=1)
        dc.set("expiring", model)

        # Backdate the timestamp
        path = dc._path("expiring")
        raw = json.loads(path.read_text())
        raw["timestamp"] = time.time() - 10
        path.write_text(json.dumps(raw))

        assert dc.get("expiring", SampleModel) is None
        assert not path.exists()

    def test_corrupted_file(self, disk_cache):
        path = disk_cache._path("bad")
        path.write_text("not valid json{{{")
        assert disk_cache.get("bad", SampleModel) is None

    def test_clear(self, disk_cache):
        disk_cache.set("a", SampleModel(name="a", value=1))
        disk_cache.set("b", SampleModel(name="b", value=2))
        disk_cache.clear()
        assert disk_cache.get("a", SampleModel) is None
        assert disk_cache.get("b", SampleModel) is None

    def test_clear_empty(self, disk_cache):
        disk_cache.clear()  # Should not raise

    def test_different_tokens_isolated(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        dc_a = DiskCache(token="token-a", ttl=3600)
        dc_b = DiskCache(token="token-b", ttl=3600)

        dc_a.set("stations", SampleModel(name="from_a", value=1))
        dc_b.set("stations", SampleModel(name="from_b", value=2))

        result_a = dc_a.get("stations", SampleModel)
        result_b = dc_b.get("stations", SampleModel)
        assert result_a.name == "from_a"
        assert result_b.name == "from_b"

    def test_ttl_from_env(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "mcp_server_tempest.cache.user_cache_dir",
            lambda app_name: str(tmp_path),
        )
        monkeypatch.setenv("WEATHERFLOW_DISK_CACHE_TTL", "7200")
        dc = DiskCache(token="test-token")
        assert dc.ttl == 7200

    def test_key_sanitization(self, disk_cache):
        model = SampleModel(name="sneaky", value=99)
        disk_cache.set("../../etc/passwd", model)
        # Should be stored safely within cache dir
        result = disk_cache.get("../../etc/passwd", SampleModel)
        assert result is not None
        assert result.name == "sneaky"
        # Verify no files were created outside cache dir
        assert all(p.parent == disk_cache.cache_dir for p in disk_cache.cache_dir.iterdir())
