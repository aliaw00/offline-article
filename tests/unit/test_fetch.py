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

    assert cache.get(url) is None
    cache.set(url, content, content_type)
    cached = cache.get(url)

    assert cached is not None
    assert cached[0] == content
    assert cached[1] == content_type

    cache.clear()
    assert cache.get(url) is None


def test_resource_fetcher_with_cache(tmp_path: Path) -> None:
    """Tests that ResourceFetcher reads from and writes to the DiskCache."""
    cache = DiskCache(tmp_path)
    url = "https://example.com/test-cached-resource"
    content = b"CACHED_CONTENT"
    content_type = "text/plain"

    cache.set(url, content, content_type)
    fetcher = ResourceFetcher(cache=cache)

    res_content, res_type = fetcher.fetch(url)

    assert res_content == content
    assert res_type == content_type
    fetcher.close()


def test_resource_fetcher_retries(local_server: str) -> None:
    """Tests that ResourceFetcher still raises after its configured retry budget."""
    bad_url = f"{local_server}/non-existent-resource-12345"
    fetcher = ResourceFetcher(timeout=2)

    with pytest.raises(FetchError):
        fetcher.fetch(bad_url, retries=1)

    fetcher.close()


def test_resource_fetcher_fetch_many_skips_failed_assets(local_server: str) -> None:
    """A single missing asset must not fail the complete concurrent batch."""
    fetcher = ResourceFetcher(timeout=2, max_connections=4)
    urls = [
        f"{local_server}/logo.png",
        f"{local_server}/bg.png",
        f"{local_server}/missing.png",
    ]

    successful, failed = fetcher.fetch_many(urls, max_workers=4, retries=0)

    assert set(successful) == {f"{local_server}/logo.png", f"{local_server}/bg.png"}
    assert set(failed) == {f"{local_server}/missing.png"}
    fetcher.close()


def test_resource_fetcher_fetch_many_deduplicates_urls(local_server: str) -> None:
    """Duplicate URLs should be downloaded once and returned once."""
    fetcher = ResourceFetcher(timeout=2, max_connections=2)
    url = f"{local_server}/logo.png"

    successful, failed = fetcher.fetch_many([url, url, url], max_workers=2, retries=0)

    assert set(successful) == {url}
    assert failed == {}
    fetcher.close()
