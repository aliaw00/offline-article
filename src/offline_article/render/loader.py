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

            wait_until_literal = cast(Literal["commit", "domcontentloaded", "load", "networkidle"], wait_until_value)
            response = page.goto(url, wait_until=wait_until_literal, timeout=timeout_ms)
            if not response:
                raise RenderError(f"No response received from {url}")

            if response.status >= 400:
                logger.warning(f"Page returned HTTP status code {response.status}")

            # Check if login is required and handle manual interactive login tab workflow
            if self.is_login_required(page):
                if not self.config.interactive:
                    logger.warning(
                        f"Authentication required for {url}, but interactive mode is not enabled. "
                        "Please run with '--interactive' or use 'auth-login' first."
                    )
                else:
                    logger.info("Authentication detected! Opening temporary tab for manual login...")
                    login_tab = context.new_page()
                    try:
                        login_tab.goto(page.url)
                        print("\n" + "=" * 80)
                        print(" [MANUAL LOGIN FLOW ACTIVE]")
                        print(f" Detected login page: {page.url}")
                        print(" Please complete manual login in the browser window/tab.")
                        print(" We will automatically detect when you are finished.")
                        print("=" * 80 + "\n")

                        import time

                        authenticated = False
                        for _ in range(120):
                            if login_tab.is_closed():
                                break
                            if not self.is_login_required(login_tab):
                                authenticated = True
                                break
                            time.sleep(1)

                        # Close temporary login tab after capture/authentication detection
                        try:
                            login_tab.close()
                        except Exception:
                            pass

                        if authenticated:
                            logger.info("Authenticated state detected! Reloading target page...")
                            response = page.goto(url, wait_until=wait_until_literal, timeout=timeout_ms)
                            if not response:
                                raise RenderError(f"No response received from {url} after re-navigation")
                        else:
                            logger.warning("Manual login timeout or cancelled.")
                    except Exception as le:
                        logger.warning(f"Error in manual login flow: {le}")

            # Optional scroll down to trigger lazy loading
            if self.config.scroll:
                self._scroll_page(page)

            return page
        except Exception as e:
            logger.error(f"Error loading page {url}: {e}")
            raise RenderError(f"Error loading page {url}: {e}") from e

    def is_login_required(self, page: Page) -> bool:
        """Determines if the page is currently a login or authentication page."""
        try:
            current_url = page.url.lower()
            if any(k in current_url for k in ["login", "signin", "auth", "oauth", "sign-in", "log-in"]):
                return True
            # Check for password input fields
            if page.locator("input[type='password']").count() > 0:
                return True
        except Exception:
            pass
        return False

    def _scroll_page(self, page: Page) -> None:
        """Scrolls the page down incrementally to trigger lazy loading and infinite scroll content."""
        try:
            logger.info("Scrolling page to trigger lazy loading...")
            page.evaluate(
                """
                async () => {
                    await new Promise((resolve) => {
                        let lastHeight = document.body.scrollHeight;
                        let noChangeCount = 0;
                        let scrollsCount = 0;
                        const maxScrolls = 30; // safety limit to prevent infinite loops

                        const timer = setInterval(() => {
                            window.scrollBy(0, window.innerHeight);
                            scrollsCount++;

                            let newHeight = document.body.scrollHeight;
                            if (newHeight === lastHeight) {
                                noChangeCount++;
                            } else {
                                noChangeCount = 0;
                                lastHeight = newHeight;
                            }

                            if (noChangeCount >= 3 || scrollsCount >= maxScrolls) {
                                clearInterval(timer);
                                resolve();
                            }
                        }, 150);
                    });
                }
                """
            )
            # Wait for network idle again after scrolling
            wait_until_value = self.config.wait_until
            if wait_until_value in ["load", "domcontentloaded", "networkidle"]:
                state_literal = cast(Literal["domcontentloaded", "load", "networkidle"], wait_until_value)
                try:
                    page.wait_for_load_state(state=state_literal, timeout=5000)
                except Exception:
                    logger.debug("Timeout waiting for load state after scroll, proceeding anyway.")
        except Exception as e:
            logger.warning(f"Scrolling page failed: {e}")
