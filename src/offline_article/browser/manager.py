import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from playwright.sync_api import BrowserContext, sync_playwright

from offline_article.config import CaptureConfig
from offline_article.exceptions import BrowserError

logger = logging.getLogger("offline-article.browser")


class BrowserManager:
    """Manages the lifecycle and session context of the Playwright browser."""

    def __init__(self, config: CaptureConfig):
        self.config = config

    @contextmanager
    def session(self) -> Generator[BrowserContext, None, None]:
        """Context manager that yields a browser context, ensuring clean shutdown."""
        with sync_playwright() as p:
            browser_type_name = self.config.browser.lower()
            if not hasattr(p, browser_type_name):
                raise BrowserError(f"Unsupported browser type: {self.config.browser}")

            browser_type = getattr(p, browser_type_name)

            # Setup proxy server settings
            from playwright.sync_api import ProxySettings

            proxy_settings: ProxySettings | None = None
            if self.config.proxy:
                proxy_settings = {"server": self.config.proxy}

            # If interactive or debug mode is on, run headful (headless=False)
            headless = not self.config.interactive and not self.config.debug

            launch_args: dict[str, Any] = {
                "headless": headless,
            }
            if proxy_settings:
                launch_args["proxy"] = proxy_settings

            context_args: dict[str, Any] = {}
            if self.config.user_agent:
                context_args["user_agent"] = self.config.user_agent

            if self.config.profile_path:
                logger.info(f"Launching persistent browser context using profile: {self.config.profile_path}")
                self.config.profile_path.mkdir(parents=True, exist_ok=True)

                # Persistent contexts take both launch options and context options
                all_args = {**launch_args, **context_args}
                context = browser_type.launch_persistent_context(
                    user_data_dir=str(self.config.profile_path), **all_args
                )
                try:
                    yield context
                finally:
                    logger.info("Closing persistent browser context...")
                    context.close()
            else:
                logger.info(f"Launching browser: {browser_type_name}")
                browser = browser_type.launch(**launch_args)
                try:
                    logger.info("Creating browser context...")
                    context = browser.new_context(**context_args)
                    yield context
                finally:
                    logger.info("Closing browser context and browser...")
                    context.close()
                    browser.close()
