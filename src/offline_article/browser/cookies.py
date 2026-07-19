import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("offline-article.browser.cookies")


def parse_netscape_cookies(content: str) -> list[dict[str, Any]]:
    """
    Parses a Netscape-formatted cookie file contents.
    Netscape format is tab-separated:
    domain  flag  path  secure  expiration  name  value
    """
    cookies = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        parts = line.split("\t")
        if len(parts) >= 7:
            domain, flag, path, secure, expiration, name, value = parts[:7]

            # Map domain prefix dots correctly
            cookie: dict[str, Any] = {
                "name": name,
                "value": value,
                "domain": domain,
                "path": path,
                "secure": secure.upper() == "TRUE",
            }

            if expiration.isdigit():
                cookie["expires"] = int(expiration)

            cookies.append(cookie)

    return cookies


def load_cookies_from_file(cookies_path: Path) -> list[dict[str, Any]]:
    """Loads cookies from either JSON or Netscape format cookie files."""
    if not cookies_path.is_file():
        logger.warning(f"Cookies file not found: {cookies_path}")
        return []

    try:
        content = cookies_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to read cookies file {cookies_path}: {e}")
        return []

    # 1. Try parsing as JSON first
    try:
        cookies = json.loads(content)
        if isinstance(cookies, list):
            logger.info(f"Loaded {len(cookies)} cookies from JSON file: {cookies_path}")
            return cookies
    except json.JSONDecodeError:
        pass

    # 2. Fallback to Netscape cookie parser
    try:
        cookies = parse_netscape_cookies(content)
        logger.info(f"Loaded {len(cookies)} cookies from Netscape file: {cookies_path}")
        return cookies
    except Exception as e:
        logger.error(f"Failed to parse Netscape cookies from {cookies_path}: {e}")

    return []


def save_cookies_to_file(cookies: list[Any], cookies_path: Path) -> None:
    """Saves cookies list back to a JSON file on disk."""
    try:
        if cookies_path.parent:
            cookies_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cookies_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)

        logger.info(f"Saved {len(cookies)} cookies to {cookies_path}")
    except Exception as e:
        logger.error(f"Failed to save cookies to {cookies_path}: {e}")
