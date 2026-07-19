import logging
from pathlib import Path

from offline_article.archive import ArchiveWriterFactory
from offline_article.browser import BrowserManager
from offline_article.config import CaptureConfig
from offline_article.discover import ResourceDiscoverer
from offline_article.exceptions import ArchiveError
from offline_article.fetch import DiskCache, ResourceFetcher
from offline_article.render import PageLoader

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
        3. Discovers resources (HTML + CSS imports recursively)
        4. Fetches all assets using browser session details
        5. Rewrites and archives resources into the target format using Strategy Pattern
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

        # 2. Setup local disk cache and ResourceFetcher using session credentials
        cache = DiskCache(self.config.cache_dir)
        fetcher = ResourceFetcher(
            cookies=cookies,
            user_agent=user_agent,
            timeout=self.config.timeout,
            proxy=self.config.proxy,
            cache=cache,
        )

        # 3. Discover all resources (HTML + CSS recursive imports)
        discoverer = ResourceDiscoverer()

        def css_fetch_for_discovery(css_url: str) -> str | None:
            try:
                data, _ = fetcher.fetch(css_url)
                return data.decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning(f"Failed to fetch CSS for discovery {css_url}: {e}")
                return None

        logger.info("Discovering all page assets...")
        discovered = discoverer.discover_all(html_content, url, css_fetch_for_discovery)

        # Flatten sets of URLs into a single set of unique absolute URLs to download
        all_urls = set()
        for urls in discovered.values():
            all_urls.update(urls)

        # 4. Fetch all discovered resource assets
        assets: dict[str, tuple[bytes, str]] = {}
        for asset_url in all_urls:
            # Skip the main page itself if it's returned in the discovered set
            if asset_url == url:
                continue
            try:
                data, mime = fetcher.fetch(asset_url)
                assets[asset_url] = (data, mime)
            except Exception as e:
                logger.warning(f"Failed to fetch asset {asset_url} during capture: {e}")

        # Close fetcher session
        fetcher.close()

        # 5. Write to output using the selected Strategy format writer
        try:
            writer = ArchiveWriterFactory.get_writer(self.config.format)
            saved_path = writer.write(html_content, url, assets, output_path)
            logger.info(f"Successfully saved captured page to {saved_path}")
            return saved_path
        except Exception as e:
            logger.error(f"Failed to write output to {output_path}: {e}")
            raise ArchiveError(f"Failed to write output to {output_path}: {e}") from e
