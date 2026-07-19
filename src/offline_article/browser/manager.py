import logging
from collections.abc import Generator
from contextlib import contextmanager

from playwright.sync_api import Browser, BrowserContext, Playwright, sync_playwright

from offline_article.config import CaptureConfig
from offline_article.exceptions import BrowserError

logger = logging.getLogger("offline-article.browser")


class BrowserManager:
    """Manages the lifecycle of the Playwright browser session."""

    def __init__(self, config: CaptureConfig):
        self.config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    def start(self) -> Browser:
        """Starts Playwright and launches the browser."""
        try:
            logger.info("Initializing Playwright...")
            self._playwright = sync_playwright().start()

            browser_type = self.config.browser.lower()
            logger.info(f"Launching browser: {browser_type}")

            from playwright.sync_api import ProxySettings

            proxy_settings: ProxySettings | None = None
            if self.config.proxy:
                proxy_settings = {"server": self.config.proxy}

            if browser_type == "chromium":
                self._browser = self._playwright.chromium.launch(headless=True, proxy=proxy_settings)
            elif browser_type == "firefox":
                self._browser = self._playwright.firefox.launch(headless=True, proxy=proxy_settings)
            elif browser_type == "webkit":
                self._browser = self._playwright.webkit.launch(headless=True, proxy=proxy_settings)
            else:
                raise BrowserError(f"Unsupported browser type: {self.config.browser}")

            return self._browser
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            self.stop()
            raise BrowserError(f"Failed to start browser: {e}") from e

    def stop(self) -> None:
        """Stops the browser and Playwright."""
        if self._browser:
            try:
                logger.info("Closing browser...")
                self._browser.close()
            except Exception as e:
                logger.warning(f"Error while closing browser: {e}")
            self._browser = None

        if self._playwright:
            try:
                logger.info("Stopping Playwright...")
                self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error while stopping Playwright: {e}")
            self._playwright = None

    @contextmanager
    def session(self) -> Generator[BrowserContext, None, None]:
        """Context manager that yields a browser context, ensuring clean shutdown."""
        self.start()
        try:
            assert self._browser is not None

            # Create a new context
            logger.info("Creating browser context...")
            context = self._browser.new_context(user_agent=self.config.user_agent)

            # TODO: Load cookies from cookies_path if specified in Phase 3/6

            yield context

            logger.info("Closing browser context...")
            context.close()
        finally:
            self.stop()
