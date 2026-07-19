import base64
import logging
import time
from typing import Any

import httpx

from offline_article.exceptions import FetchError
from offline_article.fetch.cache import DiskCache

logger = logging.getLogger("offline-article.fetch")


class ResourceFetcher:
    """Retrieves external resources using HTTPX with browser cookies, headers, and retries."""

    def __init__(
        self,
        cookies: list[Any] | None = None,
        user_agent: str | None = None,
        timeout: int = 15,
        proxy: str | None = None,
        cache: DiskCache | None = None,
    ) -> None:
        self.timeout = timeout
        self.cache = cache
        default_ua = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.headers = {
            "User-Agent": user_agent or default_ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Configure client options
        client_kwargs: dict[str, Any] = {
            "headers": self.headers,
            "timeout": self.timeout,
            "follow_redirects": True,
        }

        if proxy:
            client_kwargs["proxy"] = proxy

        self.client = httpx.Client(**client_kwargs)

        # Apply Playwright cookies to HTTPX Client
        if cookies:
            for c in cookies:
                name = c.get("name", "")
                value = c.get("value", "")
                domain = c.get("domain", "")
                path = c.get("path", "/")
                if name and value:
                    self.client.cookies.set(name, value, domain=domain, path=path)

    def fetch(self, url: str) -> tuple[bytes, str]:
        """
        Fetches the content of a resource with exponential backoff retries.
        Returns a tuple of (content_bytes, content_type_string).
        """
        if self.cache:
            cached = self.cache.get(url)
            if cached is not None:
                return cached

        retries = 3
        backoff = 1.0

        for i in range(retries):
            try:
                logger.info(f"Fetching: {url}")
                response = self.client.get(url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "application/octet-stream")
                content = response.content

                if self.cache:
                    self.cache.set(url, content, content_type)

                return content, content_type
            except Exception as e:
                if i == retries - 1:
                    logger.error(f"Failed to fetch {url} after {retries} attempts: {e}")
                    raise FetchError(f"Failed to fetch {url}: {e}") from e

                logger.warning(f"Attempt {i + 1} failed for {url}: {e}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2.0

        raise FetchError(f"Failed to fetch {url}")

    def close(self) -> None:
        """Closes the underlying HTTPX client session."""
        self.client.close()


def to_data_uri(content: bytes, content_type: str) -> str:
    """Converts resource bytes and MIME type to a base64 data URI."""
    mime = content_type.split(";")[0].strip()
    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:{mime};base64,{encoded}"
