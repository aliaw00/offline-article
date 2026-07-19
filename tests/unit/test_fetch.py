from pathlib import Path

import pytest

from offline_article.exceptions import FetchError
from offline_article.fetch.cache import DiskCache
from offline_article.fetch.client import ResourceFetcher


def test_disk_cache(tmp_path: Path) -> None:
    """Tests that DiskCache correctly caches, retrieves, and clears resources."""
    cache = DiskCache(tmp_path)
    url = "https://example.com/logo.png"
    content = b"FAKE_PNG_BYTES"
    content_type = "image/png"

    # 1. Initially uncached
    assert cache.get(url) is None

    # 2. Set cache and retrieve
    cache.set(url, content, content_type)
    cached = cache.get(url)

    assert cached is not None
    assert cached[0] == content
    assert cached[1] == content_type

    # 3. Clear cache
    cache.clear()
    assert cache.get(url) is None


def test_resource_fetcher_with_cache(tmp_path: Path) -> None:
    """Tests that ResourceFetcher reads from and writes to the DiskCache."""
    cache = DiskCache(tmp_path)
    url = "https://example.com/test-cached-resource"
    content = b"CACHED_CONTENT"
    content_type = "text/plain"

    # Pre-populate cache so fetcher doesn't need to make network request
    cache.set(url, content, content_type)

    fetcher = ResourceFetcher(cache=cache)

    # Fetch should hit cache and succeed without network error (even though client is not mock-requested)
    res_content, res_type = fetcher.fetch(url)

    assert res_content == content
    assert res_type == content_type

    fetcher.close()


def test_resource_fetcher_retries(local_server: str) -> None:
    """Tests that ResourceFetcher retries on network failures before raising FetchError."""
    # We pass a non-existent URL so that it fails
    bad_url = f"{local_server}/non-existent-resource-12345"

    fetcher = ResourceFetcher(timeout=2)

    # Should fail and raise FetchError after 3 retries
    with pytest.raises(FetchError):
        fetcher.fetch(bad_url)

    fetcher.close()
