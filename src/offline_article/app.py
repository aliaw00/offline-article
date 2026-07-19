import logging
from pathlib import Path

from offline_article.config import CaptureConfig

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
        # TODO: Implement full pipeline
        # Raise NotImplementedError or just return a mock path for skeleton testing
        if output_path is None:
            # Generate a default file name
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.netloc.replace(".", "_") or "page"
            path = parsed.path.strip("/").replace("/", "_")
            filename = f"{host}_{path}" if path else host
            output_path = Path(f"{filename}.{self.config.format}")

        logger.info(f"Target output file: {output_path}")
        return output_path
