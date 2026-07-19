import logging
from pathlib import Path

from offline_article.browser import BrowserManager
from offline_article.config import CaptureConfig
from offline_article.exceptions import ArchiveError
from offline_article.fetch import ResourceFetcher, to_data_uri
from offline_article.render import PageLoader
from offline_article.rewrite import inline_html_resources

logger = logging.getLogger("offline-article")


class App:
    """
    Main orchestrator for the offline-article capture pipeline.
    """

    def __init__(self, config: CaptureConfig):
        self.config = config

    def run(self, url: str, output_path: Path | None = None) -> Path:
        """
        Orchestrates the entire capture pipeline:
        1. Launches browser
        2. Renders and loads page
        3. Discovers resources
        4. Fetches and caches resources
        5. Rewrites and inlines resources
        6. Writes to requested archive format
        7. Validates output
        """
        logger.info(f"App running capture for URL: {url} with configuration")

        if output_path is None:
            # Generate a default file name
            from urllib.parse import urlparse

            parsed = urlparse(url)
            host = parsed.netloc.replace(".", "_") or "page"
            path = parsed.path.strip("/").replace("/", "_")
            filename = f"{host}_{path}" if path else host
            output_path = Path(f"{filename}.{self.config.format}")

        logger.info(f"Target output file: {output_path}")

        # Initialize browser manager and page loader
        browser_manager = BrowserManager(self.config)
        page_loader = PageLoader(self.config)

        html_content = ""
        cookies = []
        user_agent = None

        # 1. Run render pipeline in browser context
        with browser_manager.session() as context:
            page = page_loader.load_page(context, url)
            logger.info("Extracting rendered page content...")
            html_content = page.content()

            # Retrieve session cookies and user-agent
            cookies = context.cookies()
            try:
                user_agent = page.evaluate("navigator.userAgent")
            except Exception as e:
                logger.warning(f"Could not retrieve user agent from browser: {e}")

        # 2. Setup ResourceFetcher using session credentials
        fetcher = ResourceFetcher(
            cookies=cookies,
            user_agent=user_agent,
            timeout=self.config.timeout,
            proxy=self.config.proxy,
        )

        # Caches to avoid duplicate fetches for shared resources
        text_cache: dict[str, str] = {}
        data_uri_cache: dict[str, str] = {}

        def fetch_text_callback(resource_url: str) -> str | None:
            if resource_url in text_cache:
                return text_cache[resource_url]
            try:
                content_bytes, _ = fetcher.fetch(resource_url)
                content_str = content_bytes.decode("utf-8", errors="replace")
                text_cache[resource_url] = content_str
                return content_str
            except Exception as e:
                logger.warning(f"Failed to fetch text resource {resource_url}: {e}")
                return None

        def fetch_data_uri_callback(resource_url: str) -> str | None:
            if resource_url in data_uri_cache:
                return data_uri_cache[resource_url]
            try:
                content_bytes, content_type = fetcher.fetch(resource_url)
                data_uri = to_data_uri(content_bytes, content_type)
                data_uri_cache[resource_url] = data_uri
                return data_uri
            except Exception as e:
                logger.warning(f"Failed to fetch data URI resource {resource_url}: {e}")
                return None

        # 3. Compile HTML by inlining all assets
        try:
            logger.info("Inlining page resources...")
            compiled_html = inline_html_resources(
                html_content,
                url,
                fetch_text=fetch_text_callback,
                fetch_data_uri=fetch_data_uri_callback,
            )
        finally:
            fetcher.close()

        # 4. Save compiled HTML to file
        try:
            if output_path.parent:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(compiled_html)
            logger.info(f"Successfully saved compiled page to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write output to {output_path}: {e}")
            raise ArchiveError(f"Failed to write output to {output_path}: {e}") from e

        return output_path
