import hashlib
import logging
import mimetypes
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from offline_article.archive.base import ArchiveWriter
from offline_article.discover.html import get_str_attr, normalize_url
from offline_article.exceptions import ArchiveError

logger = logging.getLogger("offline-article.archive.dir")

URL_REGEX = re.compile(r"url\(\s*['\"]?(.*?)['\"]?\s*\)", re.IGNORECASE)


def get_safe_filename(url: str, content_type: str, hash_override: str | None = None) -> str:
    """Generates a unique, clean, and safe filename for an asset based on URL and MIME type."""
    parsed = urlparse(url)
    mime = content_type.split(";")[0].strip()
    ext = mimetypes.guess_extension(mime) or ""

    # Fallback common extensions
    if not ext:
        if "javascript" in mime:
            ext = ".js"
        elif "css" in mime:
            ext = ".css"
        elif "html" in mime:
            ext = ".html"

    hasher = hash_override or hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    orig_name = Path(parsed.path).stem
    # Filter only alphanumeric, hyphens, and underscores
    orig_name = "".join(c for c in orig_name if c.isalnum() or c in ("-", "_"))[:20]

    if orig_name:
        return f"{orig_name}_{hasher}{ext}"
    return f"asset_{hasher}{ext}"


class DirWriter(ArchiveWriter):
    """Saves the page in an extracted directory with an index.html and assets/ subfolder."""

    def write(
        self,
        html_content: str,
        base_url: str,
        assets: dict[str, tuple[bytes, str]],
        output_path: Path,
    ) -> Path:
        logger.info(f"Writing offline directory to: {output_path}")

        try:
            # 1. Create target directory and assets subfolder
            output_path.mkdir(parents=True, exist_ok=True)
            assets_dir = output_path / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            url_to_relative: dict[str, str] = {}

            # Map from content hash to relative filename path to avoid writing duplicate assets
            hash_to_relative: dict[str, str] = {}

            # 2. Write assets to local files and populate mapping (deduplicated by content hash)
            for url, (data, mime) in assets.items():
                if url == base_url:
                    continue
                content_hash = hashlib.sha256(data).hexdigest()[:12]

                if content_hash in hash_to_relative:
                    url_to_relative[url] = hash_to_relative[content_hash]
                    continue

                filename = get_safe_filename(url, mime, hash_override=content_hash)
                asset_file_path = assets_dir / filename

                # Write data to file
                with open(asset_file_path, "wb") as f_asset:
                    f_asset.write(data)

                rel_path = f"assets/{filename}"
                hash_to_relative[content_hash] = rel_path
                url_to_relative[url] = rel_path

            # 3. Rewrite CSS files with relative url() paths from their local perspective
            for url, (data, mime) in assets.items():
                if url == base_url or "css" not in mime.lower():
                    continue

                filename = get_safe_filename(url, mime)
                local_css_path = assets_dir / filename

                css_text = data.decode("utf-8", errors="replace")

                def replace_css_url(match: re.Match, current_url: str = url) -> str:
                    css_url = match.group(1)
                    if not css_url or css_url.lower().startswith("data:") or css_url.startswith("#"):
                        return match.group(0)

                    abs_asset_url = normalize_url(current_url, css_url)
                    if abs_asset_url in url_to_relative:
                        # Since CSS is in assets/ and asset is in assets/, path is just the filename
                        rel_name = Path(url_to_relative[abs_asset_url]).name
                        return f"url('{rel_name}')"
                    return match.group(0)

                rewritten_css = URL_REGEX.sub(replace_css_url, css_text)

                with open(local_css_path, "w", encoding="utf-8") as f_css:
                    f_css.write(rewritten_css)

            # 4. Parse HTML and rewrite asset links
            soup = BeautifulSoup(html_content, "lxml")

            def rewrite_attr(element: Any, attr_name: str) -> None:
                val = get_str_attr(element, attr_name)
                if val:
                    abs_url = normalize_url(base_url, val)
                    if abs_url in url_to_relative:
                        element[attr_name] = url_to_relative[abs_url]

            # Rewrite tags
            for link in soup.find_all("link"):
                rewrite_attr(link, "href")
            for script in soup.find_all("script"):
                rewrite_attr(script, "src")
            for img in soup.find_all("img"):
                rewrite_attr(img, "src")
                srcset = get_str_attr(img, "srcset")
                if srcset:
                    parts = []
                    for part in srcset.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        tokens = part.split()
                        if tokens:
                            img_url = tokens[0]
                            abs_url = normalize_url(base_url, img_url)
                            if abs_url in url_to_relative:
                                tokens[0] = url_to_relative[abs_url]
                            parts.append(" ".join(tokens))
                    if parts:
                        img["srcset"] = ", ".join(parts)

            for svg_img in soup.find_all("image"):
                attr = "href" if svg_img.has_attr("href") else "xlink:href"
                rewrite_attr(svg_img, attr)

            for source in soup.find_all("source"):
                rewrite_attr(source, "src")
                srcset = get_str_attr(source, "srcset")
                if srcset:
                    parts = []
                    for part in srcset.split(","):
                        part = part.strip()
                        if not part:
                            continue
                        tokens = part.split()
                        if tokens:
                            img_url = tokens[0]
                            abs_url = normalize_url(base_url, img_url)
                            if abs_url in url_to_relative:
                                tokens[0] = url_to_relative[abs_url]
                            parts.append(" ".join(tokens))
                    if parts:
                        source["srcset"] = ", ".join(parts)

            for iframe in soup.find_all("iframe"):
                rewrite_attr(iframe, "src")

            for meta in soup.find_all("meta"):
                content = get_str_attr(meta, "content")
                if content:
                    abs_url = normalize_url(base_url, content)
                    if abs_url in url_to_relative:
                        meta["content"] = url_to_relative[abs_url]

            # Rewrite inline style attributes
            for tag in soup.find_all(style=True):
                style_attr = get_str_attr(tag, "style")
                if style_attr:

                    def replace_inline_style_url(match: re.Match) -> str:
                        inline_url = match.group(1)
                        if not inline_url or inline_url.lower().startswith("data:") or inline_url.startswith("#"):
                            return match.group(0)
                        abs_asset_url = normalize_url(base_url, inline_url)
                        if abs_asset_url in url_to_relative:
                            return f"url('{url_to_relative[abs_asset_url]}')"
                        return match.group(0)

                    tag["style"] = URL_REGEX.sub(replace_inline_style_url, style_attr)

            # Rewrite style tags
            for style in soup.find_all("style"):
                if style.string:

                    def replace_style_tag_url(match: re.Match) -> str:
                        style_url = match.group(1)
                        if not style_url or style_url.lower().startswith("data:") or style_url.startswith("#"):
                            return match.group(0)
                        abs_asset_url = normalize_url(base_url, style_url)
                        if abs_asset_url in url_to_relative:
                            return f"url('{url_to_relative[abs_asset_url]}')"
                        return match.group(0)

                    style.string = URL_REGEX.sub(replace_style_tag_url, style.string)

            # 5. Write the index.html file
            index_path = output_path / "index.html"
            with open(index_path, "w", encoding="utf-8") as f_html:
                f_html.write(str(soup))

            return index_path
        except Exception as e:
            logger.error(f"Failed to write offline directory: {e}")
            raise ArchiveError(f"Failed to write offline directory: {e}") from e
