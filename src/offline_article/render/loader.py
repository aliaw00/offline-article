import logging

from typing import Literal, cast

from playwright.sync_api import BrowserContext, Page

from offline_article.config import CaptureConfig
from offline_article.exceptions import RenderError

logger = logging.getLogger("offline-article.render")


class PageLoader:
    """Handles page navigation, load waiting, and stabilization."""

    def __init__(self, config: CaptureConfig):
        self.config = config

    def load_page(self, context: BrowserContext, url: str) -> Page:
        """
        Creates a new page in the context, navigates to the URL, and waits for completion.
        """
        try:
            logger.info(f"Opening page for URL: {url}")
            page = context.new_page()

            # Configure JS/Images based on configuration
            if self.config.no_js:
                logger.info("Disabling JavaScript execution on page...")
                # Playwright doesn't allow disabling JS mid-context, but we can do it via routing
                # or context creation. For now, we note this restriction.
                # (Disabling JS is usually done during new_context creation if supported).
                pass

            # Set page load timeouts (in milliseconds)
            timeout_ms = self.config.timeout * 1000
            page.set_default_timeout(timeout_ms)

            # Navigate to the URL
            logger.info(f"Navigating to {url}...")
            # wait_until can be: "load", "domcontentloaded", "networkidle"
            wait_until_value = self.config.wait_until
            if wait_until_value not in ["load", "domcontentloaded", "networkidle"]:
                wait_until_value = "networkidle"

            wait_until_literal = cast(
                Literal["commit", "domcontentloaded", "load", "networkidle"], wait_until_value
            )
            response = page.goto(url, wait_until=wait_until_literal, timeout=timeout_ms)
            if not response:
                raise RenderError(f"No response received from {url}")

            if response.status >= 400:
                logger.warning(f"Page returned HTTP status code {response.status}")

            # Optional scroll down to trigger lazy loading
            if self.config.scroll:
                self._scroll_page(page)

            return page
        except Exception as e:
            logger.error(f"Error loading page {url}: {e}")
            raise RenderError(f"Error loading page {url}: {e}") from e

    def _scroll_page(self, page: Page) -> None:
        """Scrolls the page down incrementally to trigger lazy loading."""
        try:
            logger.info("Scrolling page to trigger lazy loading...")
            # Simple scrolling script
            page.evaluate(
                """
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            if(totalHeight >= scrollHeight - window.innerHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
                """
            )
            # Wait for network idle again after scrolling
            wait_until_value = self.config.wait_until
            if wait_until_value in ["load", "domcontentloaded", "networkidle"]:
                state_literal = cast(
                    Literal["domcontentloaded", "load", "networkidle"], wait_until_value
                )
                page.wait_for_load_state(state=state_literal, timeout=5000)
        except Exception as e:
            logger.warning(f"Scrolling page failed: {e}")
