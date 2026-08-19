import base64
import logging
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import httpx

from offline_article.exceptions import FetchError
from offline_article.fetch.cache import DiskCache

logger = logging.getLogger("offline-article.fetch")


class ResourceFetcher:
    """
    Retrieves external resources with connection pooling, cache support, retries,
    and optional concurrent fetching.

    The fetcher deliberately treats page assets as best-effort resources: callers
    can catch FetchError and continue building the archive when a non-critical
    image/font/script is unavailable.
    """

    def __init__(
        self,
        cookies: list[Any] | None = None,
        user_agent: str | None = None,
        timeout: int = 15,
        proxy: str | None = None,
        cache: DiskCache | None = None,
        max_connections: int = 16,
    ) -> None:
        self.timeout = timeout
        self.cache = cache
        self.max_connections = max(1, max_connections)
        default_ua = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.headers = {
            "User-Agent": user_agent or default_ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }

        limits = httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_connections,
            keepalive_expiry=30.0,
        )
        client_kwargs: dict[str, Any] = {
            "headers": self.headers,
            "timeout": self.timeout,
            "follow_redirects": True,
            "limits": limits,
        }

        if proxy:
            client_kwargs["proxy"] = proxy

        self.client = httpx.Client(**client_kwargs)

        if cookies:
            for cookie in cookies:
                name = cookie.get("name", "")
                value = cookie.get("value", "")
                domain = cookie.get("domain", "")
                path = cookie.get("path", "/")
                if name and value:
                    self.client.cookies.set(name, value, domain=domain, path=path)

    @staticmethod
    def _should_retry(exc: Exception) -> bool:
        """Returns True for transient transport/HTTP failures."""
        if isinstance(exc, (httpx.ConnectError, httpx.NetworkError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout)):
            return True
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            return status == 429 or 500 <= status <= 599
        return False

    def fetch(self, url: str, retries: int = 1, backoff: float = 0.25) -> tuple[bytes, str]:
        """
        Fetch a single resource.

        ``retries`` is the number of attempts after the first attempt. The
        default is intentionally low because page assets are optional and a
        failed asset must not stall the whole capture for seconds.
        """
        if self.cache:
            cached = self.cache.get(url)
            if cached is not None:
                return cached

        attempts = max(1, retries + 1)
        delay = max(0.0, backoff)

        for attempt in range(1, attempts + 1):
            try:
                logger.debug("Fetching resource: %s (attempt %d/%d)", url, attempt, attempts)
                response = self.client.get(url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "application/octet-stream")
                content = response.content

                if self.cache:
                    self.cache.set(url, content, content_type)

                return content, content_type
            except Exception as exc:
                retryable = self._should_retry(exc)
                if attempt >= attempts or not retryable:
                    logger.debug("Resource fetch failed: %s: %s", url, exc)
                    raise FetchError(f"Failed to fetch {url}: {exc}") from exc

                logger.debug("Transient failure for %s; retrying in %.2fs: %s", url, delay, exc)
                if delay:
                    time.sleep(delay)
                    delay *= 2.0

        raise FetchError(f"Failed to fetch {url}")

    def fetch_many(
        self,
        urls: Iterable[str],
        max_workers: int | None = None,
        retries: int = 1,
    ) -> tuple[dict[str, tuple[bytes, str]], dict[str, Exception]]:
        """
        Fetch many resources concurrently.

        Returns ``(successful, failed)`` mappings. A failed asset is never
        allowed to abort the whole batch.
        """
        unique_urls = sorted({url for url in urls if url})
        if not unique_urls:
            return {}, {}

        worker_count = max(1, min(max_workers or self.max_connections, len(unique_urls), self.max_connections))
        successful: dict[str, tuple[bytes, str]] = {}
        failed: dict[str, Exception] = {}

        logger.info("Fetching %d resources with %d concurrent workers", len(unique_urls), worker_count)

        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="asset-fetch") as executor:
            future_to_url = {
                executor.submit(self.fetch, url, retries, 0.25): url for url in unique_urls
            }
            for future in as_completed(future_to_url):
                asset_url = future_to_url[future]
                try:
                    successful[asset_url] = future.result()
                except Exception as exc:
                    failed[asset_url] = exc
                    logger.warning("Skipping unavailable asset %s: %s", asset_url, exc)

        return successful, failed

    def close(self) -> None:
        """Closes the underlying HTTPX client session."""
        self.client.close()


def to_data_uri(content: bytes, content_type: str) -> str:
    """Converts resource bytes and MIME type to a base64 data URI."""
    mime = content_type.split(";", 1)[0].strip() or "application/octet-stream"
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{mime};base64,{encoded}"
