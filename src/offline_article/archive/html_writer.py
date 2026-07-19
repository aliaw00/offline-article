import logging
from pathlib import Path

from offline_article.archive.base import ArchiveWriter
from offline_article.exceptions import ArchiveError
from offline_article.fetch.client import to_data_uri
from offline_article.rewrite.html import inline_html_resources

logger = logging.getLogger("offline-article.archive.html")


class HtmlWriter(ArchiveWriter):
    """Writes the page as a single self-contained HTML file with base64 inlined assets."""

    def write(
        self,
        html_content: str,
        base_url: str,
        assets: dict[str, tuple[bytes, str]],
        output_path: Path,
    ) -> Path:
        logger.info(f"Writing single-file HTML to: {output_path}")

        def fetch_text_callback(url: str) -> str | None:
            if url == base_url:
                return html_content
            if url in assets:
                content_bytes, _ = assets[url]
                return content_bytes.decode("utf-8", errors="replace")
            return None

        def fetch_data_uri_callback(url: str) -> str | None:
            if url in assets:
                content_bytes, content_type = assets[url]
                return to_data_uri(content_bytes, content_type)
            return None

        try:
            compiled_html = inline_html_resources(
                html_content,
                base_url,
                fetch_text=fetch_text_callback,
                fetch_data_uri=fetch_data_uri_callback,
            )

            # Ensure parent directories exist
            if output_path.parent:
                output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(compiled_html)

            return output_path
        except Exception as e:
            logger.error(f"Failed to write single HTML archive: {e}")
            raise ArchiveError(f"Failed to write single HTML archive: {e}") from e
