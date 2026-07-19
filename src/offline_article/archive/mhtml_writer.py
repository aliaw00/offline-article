import logging
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from offline_article.archive.base import ArchiveWriter
from offline_article.discover.html import get_str_attr, normalize_url

logger = logging.getLogger("offline-article.archive.mhtml")


class MhtmlWriter(ArchiveWriter):
    """Saves page and all assets as a single MHTML (MIME HTML) archive file (RFC 2557)."""

    def write(self, html_content: str, url: str, assets: dict[str, tuple[bytes, str]], output_path: Path) -> Path:
        logger.info(f"Saving MHTML archive to {output_path}")

        # 1. Rewrite all asset references inside the HTML to absolute URLs to match Content-Location
        soup = BeautifulSoup(html_content, "lxml")

        def rewrite_attr(tag: Any, attr: str) -> None:
            val = get_str_attr(tag, attr)
            if val and not val.lower().startswith("data:"):
                tag[attr] = normalize_url(url, val)

        for link in soup.find_all("link"):
            rewrite_attr(link, "href")
        for script in soup.find_all("script"):
            rewrite_attr(script, "src")
        for img in soup.find_all("img"):
            rewrite_attr(img, "src")
        for iframe in soup.find_all("iframe"):
            rewrite_attr(iframe, "src")

        absolute_html = str(soup)

        # 2. Construct MIME multipart/related message
        msg = MIMEMultipart("related")
        msg["From"] = "<Saved by offline-article>"
        msg["Snapshot-Content-Location"] = url
        msg["Subject"] = "Captured Page"
        msg["MIME-Version"] = "1.0"

        # Add HTML body part
        html_part = MIMEText(absolute_html, "html", "utf-8")
        html_part.add_header("Content-Location", url)
        msg.attach(html_part)

        # Add resources
        for asset_url, (data, mime) in assets.items():
            maintype, subtype = mime.split("/", 1) if "/" in mime else ("application", "octet-stream")
            part = MIMEBase(maintype, subtype)
            part.set_payload(data)
            encoders.encode_base64(part)
            part.add_header("Content-Location", asset_url)
            part.add_header("Content-Transfer-Encoding", "base64")
            msg.attach(part)

        # 3. Write MHTML file
        try:
            if output_path.parent:
                output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(msg.as_bytes())

            logger.info(f"Successfully saved {len(assets)} assets inside MHTML archive at {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to write MHTML file to {output_path}: {e}")
            raise e
