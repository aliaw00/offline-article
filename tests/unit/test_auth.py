from pathlib import Path

from offline_article.browser.cookies import load_cookies_from_file, parse_netscape_cookies, save_cookies_to_file
from offline_article.browser.manager import BrowserManager
from offline_article.config import CaptureConfig


def test_parse_netscape_cookies() -> None:
    """Tests that Netscape-formatted cookie strings are parsed correctly."""
    netscape_content = (
        "# Netscape HTTP Cookie File\n"
        ".example.com\tTRUE\t/\tFALSE\t1700000000\tsession_id\tabc123\n"
        "example.com\tFALSE\t/path\tTRUE\t0\tuser_token\txyz789\n"
    )

    cookies = parse_netscape_cookies(netscape_content)
    assert len(cookies) == 2

    assert cookies[0]["name"] == "session_id"
    assert cookies[0]["value"] == "abc123"
    assert cookies[0]["domain"] == ".example.com"
    assert cookies[0]["path"] == "/"
    assert cookies[0]["secure"] is False
    assert cookies[0]["expires"] == 1700000000

    assert cookies[1]["name"] == "user_token"
    assert cookies[1]["value"] == "xyz789"
    assert cookies[1]["domain"] == "example.com"
    assert cookies[1]["path"] == "/path"
    assert cookies[1]["secure"] is True


def test_load_save_cookies_json(tmp_path: Path) -> None:
    """Tests loading and saving cookies in JSON format."""
    cookies_file = tmp_path / "cookies.json"
    raw_cookies = [
        {
            "name": "foo",
            "value": "bar",
            "domain": "example.com",
            "path": "/",
            "secure": True,
        }
    ]

    # Save cookies to file
    save_cookies_to_file(raw_cookies, cookies_file)
    assert cookies_file.is_file()

    # Load cookies from file
    loaded = load_cookies_from_file(cookies_file)
    assert len(loaded) == 1
    assert loaded[0]["name"] == "foo"
    assert loaded[0]["value"] == "bar"
    assert loaded[0]["domain"] == "example.com"
    assert loaded[0]["secure"] is True


def test_browser_profile_reuse(tmp_path: Path) -> None:
    """Tests that BrowserManager correctly starts a persistent browser context when profile_path is set."""
    profile_dir = tmp_path / "browser_profile"
    config = CaptureConfig(profile_path=profile_dir)
    browser_manager = BrowserManager(config)

    with browser_manager.session() as context:
        # Check that context is valid and we can create pages
        page = context.new_page()
        assert page is not None

    # Check that profile directory was created
    assert profile_dir.is_dir()
