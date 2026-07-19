import hashlib
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("offline-article.fetch.cache")


class DiskCache:
    """A simple file-based persistent disk cache for fetched resources."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_paths(self, url: str) -> tuple[Path, Path]:
        """Returns the metadata and body file paths for a given URL."""
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return (
            self.cache_dir / f"{url_hash}.metadata.json",
            self.cache_dir / f"{url_hash}.body",
        )

    def get(self, url: str) -> tuple[bytes, str] | None:
        """Retrieves a cached resource by URL if it exists, otherwise returns None."""
        meta_path, body_path = self._get_paths(url)
        if meta_path.is_file() and body_path.is_file():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    meta = json.load(f)

                content_type = meta.get("content_type", "application/octet-stream")

                with open(body_path, "rb") as f_body:
                    content = f_body.read()

                logger.debug(f"Cache hit: {url}")
                return content, content_type
            except Exception as e:
                logger.warning(f"Error reading cache for {url}: {e}")
                return None
        return None

    def set(self, url: str, content: bytes, content_type: str) -> None:
        """Stores a resource in the local disk cache."""
        meta_path, body_path = self._get_paths(url)
        try:
            meta = {
                "url": url,
                "content_type": content_type,
                "timestamp": time.time(),
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            with open(body_path, "wb") as f_body:
                f_body.write(content)

            logger.debug(f"Cache set: {url}")
        except Exception as e:
            logger.warning(f"Failed to write cache for {url}: {e}")

    def clear(self) -> None:
        """Clears all cached items from the cache directory."""
        logger.info("Clearing local disk cache...")
        for file_path in self.cache_dir.glob("*"):
            if file_path.is_file():
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {file_path}: {e}")
