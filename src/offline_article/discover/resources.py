import logging
from collections.abc import Callable

from offline_article.discover.css import discover_css_resources
from offline_article.discover.html import discover_html_resources

logger = logging.getLogger("offline-article.discover.resources")


class ResourceDiscoverer:
    """Orchestrates resource discovery from HTML and CSS content."""

    def __init__(self) -> None:
        pass

    def discover_from_html(self, html_content: str, base_url: str) -> dict[str, set[str]]:
        """
        Discovers all resource links directly referenced in the HTML:
        - stylesheets
        - scripts
        - images
        - fonts
        - iframes
        - metadata
        """
        logger.info(f"Discovering resources from HTML for base URL: {base_url}")
        return discover_html_resources(html_content, base_url)

    def discover_from_css(self, css_content: str, base_url: str) -> dict[str, set[str]]:
        """
        Discovers resources referenced in CSS content:
        - stylesheets (imports)
        - images (backgrounds)
        - fonts
        """
        logger.info(f"Discovering resources from CSS for base URL: {base_url}")
        return discover_css_resources(css_content, base_url)

    def discover_all(
        self,
        html_content: str,
        base_url: str,
        css_fetcher_callback: Callable[[str], str | None] | None = None,
    ) -> dict[str, set[str]]:
        """
        Performs full discovery:
        1. Discovers direct resources in HTML.
        2. If css_fetcher_callback is provided, fetches and parses discovered stylesheets
           to discover nested assets (imports, backgrounds, fonts).
        """
        resources = self.discover_from_html(html_content, base_url)

        if not css_fetcher_callback:
            return resources

        # Recursive resolution of stylesheets to find fonts, images, and nested imports
        processed_stylesheets = set()
        stylesheets_to_process = list(resources["stylesheets"])

        while stylesheets_to_process:
            css_url = stylesheets_to_process.pop(0)
            if css_url in processed_stylesheets:
                continue

            processed_stylesheets.add(css_url)
            try:
                logger.info(f"Fetching stylesheet for discovery: {css_url}")
                css_content = css_fetcher_callback(css_url)
                if css_content:
                    nested = self.discover_from_css(css_content, css_url)

                    # Merge discovered assets
                    resources["images"].update(nested["images"])
                    resources["fonts"].update(nested["fonts"])

                    # Add nested imports to the processing queue
                    for nested_css in nested["stylesheets"]:
                        if nested_css not in processed_stylesheets:
                            resources["stylesheets"].add(nested_css)
                            stylesheets_to_process.append(nested_css)
            except Exception as e:
                logger.warning(f"Failed to process stylesheet {css_url} during discovery: {e}")

        return resources
