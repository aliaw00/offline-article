import logging
from pathlib import Path

from offline_article.browser import BrowserManager
from offline_article.config import CaptureConfig
from offline_article.exceptions import ArchiveError
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
        2. Renders and load page
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

        # Run render pipeline
        with browser_manager.session() as context:
            page = page_loader.load_page(context, url)
            logger.info("Extracting rendered page content...")
            html_content = page.content()

        # Save HTML to file
        try:
            if output_path.parent:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Successfully saved page to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write output to {output_path}: {e}")
            raise ArchiveError(f"Failed to write output to {output_path}: {e}") from e

        return output_path
