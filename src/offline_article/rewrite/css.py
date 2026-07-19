import logging
import re
from collections.abc import Callable

from offline_article.discover.html import normalize_url

logger = logging.getLogger("offline-article.rewrite.css")

# Regex to discover url(...) references, handling optional quotes and whitespace
URL_REGEX = re.compile(r'url\(\s*[\'"]?(.*?)[\'"]?\s*\)', re.IGNORECASE)

# Regex to match @import statements, handling both direct string format and url() wrapper
IMPORT_REGEX = re.compile(
    r'@import\s+(?:url\(\s*[\'"]?(.*?)[\'"]?\s*\)|[\'"](.*?)[\'"])\s*;?',
    re.IGNORECASE,
)


def inline_css_urls(
    css_content: str,
    base_url: str,
    fetch_callback: Callable[[str, bool], str | None],
) -> str:
    """
    Recursively resolves and inlines `@import` styles and local `url()` assets (images/fonts)
    into base64 data URIs.

    - fetch_callback is a function: (url: str, is_css: bool) -> data_uri_or_css_content_str
    """

    def replace_import(match: re.Match) -> str:
        url = match.group(1) or match.group(2)
        if not url or url.lower().startswith("data:"):
            return match.group(0)

        abs_url = normalize_url(base_url, url)
        logger.info(f"Inlining nested CSS import: {abs_url}")

        # Fetch nested CSS content
        imported_css = fetch_callback(abs_url, True)
        if imported_css is not None:
            # Inline recursively
            return inline_css_urls(imported_css, abs_url, fetch_callback)
        return ""  # Remove import if fetching fails

    # 1. Inline @import statements
    css_content = IMPORT_REGEX.sub(replace_import, css_content)

    def replace_url(match: re.Match) -> str:
        url = match.group(1)
        if not url or url.lower().startswith("data:") or url.startswith("#"):
            return match.group(0)

        abs_url = normalize_url(base_url, url)
        logger.debug(f"Inlining CSS asset url(): {abs_url}")

        # Fetch asset as base64 data URI
        data_uri = fetch_callback(abs_url, False)
        if data_uri:
            return f"url('{data_uri}')"
        return match.group(0)

    # 2. Inline images and fonts in url(...)
    css_content = URL_REGEX.sub(replace_url, css_content)

    return css_content
