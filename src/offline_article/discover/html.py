import logging
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger("offline-article.discover.html")


def get_str_attr(element: Any, attr: str) -> str:
    """Safely extracts a string attribute from a BeautifulSoup element."""
    val = element.get(attr)
    if isinstance(val, list):
        return " ".join(val)
    if isinstance(val, str):
        return val
    return ""


def normalize_url(base_url: str, url: str) -> str:
    """
    Normalizes a resource URL:
    1. Makes it absolute using base_url.
    2. Strips URL fragments (e.g. #header).
    3. Normalizes path separators.
    """
    if not url:
        return ""

    # Strip whitespace
    url = url.strip()

    # Join with base URL to make absolute
    absolute_url = urljoin(base_url, url)

    # Parse and strip fragment
    parsed = urlparse(absolute_url)
    if parsed.fragment:
        parsed = parsed._replace(fragment="")
        absolute_url = parsed.geturl()

    return absolute_url


def discover_html_resources(html_content: str, base_url: str) -> dict[str, set[str]]:
    """
    Parses HTML content using BeautifulSoup and extracts resource URLs:
    - stylesheets
    - scripts
    - images
    - fonts
    - iframes
    - metadata
    """
    soup = BeautifulSoup(html_content, "lxml")

    resources: dict[str, set[str]] = {
        "stylesheets": set(),
        "scripts": set(),
        "images": set(),
        "fonts": set(),
        "iframes": set(),
        "metadata": set(),
    }

    # 1. Discover Stylesheets
    for link in soup.find_all("link"):
        rel: Any = link.get("rel") or []
        rel_list = rel if isinstance(rel, list) else [rel]
        rel_lower = [str(r).lower() for r in rel_list]

        if "stylesheet" in rel_lower:
            href = get_str_attr(link, "href")
            if href:
                resources["stylesheets"].add(normalize_url(base_url, href))

    # 2. Discover Scripts
    for script in soup.find_all("script"):
        src = get_str_attr(script, "src")
        if src:
            resources["scripts"].add(normalize_url(base_url, src))

    # 3. Discover Images
    # Standard images
    for img in soup.find_all("img"):
        src = get_str_attr(img, "src")
        if src:
            resources["images"].add(normalize_url(base_url, src))

        # Handle srcset
        srcset = get_str_attr(img, "srcset")
        if srcset:
            for part in srcset.split(","):
                part = part.strip()
                if not part:
                    continue
                url_part = part.split()[0]
                resources["images"].add(normalize_url(base_url, url_part))

    # SVGs with image tag
    for svg_img in soup.find_all("image"):
        href = get_str_attr(svg_img, "href") or get_str_attr(svg_img, "xlink:href")
        if href:
            resources["images"].add(normalize_url(base_url, href))

    # Picture sources
    for source in soup.find_all("source"):
        srcset = get_str_attr(source, "srcset")
        if srcset:
            for part in srcset.split(","):
                part = part.strip()
                if not part:
                    continue
                url_part = part.split()[0]
                resources["images"].add(normalize_url(base_url, url_part))
        src = get_str_attr(source, "src")
        if src:
            resources["images"].add(normalize_url(base_url, src))

    # 4. Discover Metadata Assets (icons, OpenGraph images, Twitter cards)
    # Icons
    icon_rels = {"icon", "shortcut", "apple-touch-icon"}
    for link in soup.find_all("link"):
        rel_val: Any = link.get("rel") or []
        rel_list = rel_val if isinstance(rel_val, list) else [rel_val]
        rel_lower = [str(r).lower() for r in rel_list]

        if any(any(icon in r for icon in icon_rels) for r in rel_lower):
            href = get_str_attr(link, "href")
            if href:
                resources["metadata"].add(normalize_url(base_url, href))

    # Meta tag images (og:image, twitter:image, etc.)
    for meta in soup.find_all("meta"):
        property_attr = get_str_attr(meta, "property")
        name_attr = get_str_attr(meta, "name")
        content = get_str_attr(meta, "content")

        if content and (
            "image" in property_attr.lower() or "image" in name_attr.lower() or "icon" in name_attr.lower()
        ):
            resources["metadata"].add(normalize_url(base_url, content))

    # 5. Discover Iframes
    for iframe in soup.find_all("iframe"):
        src = get_str_attr(iframe, "src")
        if src:
            resources["iframes"].add(normalize_url(base_url, src))

    # Clean up empty strings
    for category in resources:
        resources[category] = {url for url in resources[category] if url}

    return resources
