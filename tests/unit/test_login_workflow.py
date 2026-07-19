from unittest.mock import MagicMock

from offline_article.config import CaptureConfig
from offline_article.render.loader import PageLoader


def test_is_login_required() -> None:
    """Tests that PageLoader correctly identifies login pages based on URL and form inputs."""
    config = CaptureConfig()
    loader = PageLoader(config)

    # 1. URL contains login keywords
    page_login_url = MagicMock()
    page_login_url.url = "https://example.com/auth/login"
    page_login_url.locator.return_value.count.return_value = 0
    assert loader.is_login_required(page_login_url) is True

    # 2. Page has a password input field
    page_password_form = MagicMock()
    page_password_form.url = "https://example.com/protected-page"
    # mock locator("input[type='password']")
    page_password_form.locator.return_value.count.return_value = 1
    assert loader.is_login_required(page_password_form) is True

    # 3. Normal article page
    page_normal = MagicMock()
    page_normal.url = "https://example.com/news/123"
    page_normal.locator.return_value.count.return_value = 0
    assert loader.is_login_required(page_normal) is False


def test_load_page_interactive_login() -> None:
    """Tests that PageLoader launches and closes the manual login tab workflow correctly."""
    config = CaptureConfig(interactive=True)
    loader = PageLoader(config)

    context = MagicMock()
    page_main = MagicMock()
    page_login = MagicMock()

    # context.new_page will return page_main first, then the temporary page_login
    context.new_page.side_effect = [page_main, page_login]

    # Main page lands on login page
    page_main.url = "https://example.com/login"
    page_main.locator.return_value.count.return_value = 0
    page_main.goto.return_value = MagicMock(status=200)

    # Temporary login tab successfully transitions away from login page
    page_login.url = "https://example.com/dashboard"
    page_login.locator.return_value.count.return_value = 0
    page_login.is_closed.return_value = False

    res = loader.load_page(context, "https://example.com/dashboard")

    # Assert main tab is returned
    assert res == page_main

    # Assert temporary tab was created and navigated
    assert context.new_page.call_count == 2
    page_login.goto.assert_called_once_with("https://example.com/login")

    # Assert temporary login tab was closed correctly
    page_login.close.assert_called_once()

    # Assert main tab reloaded target page
    assert page_main.goto.call_count == 2
