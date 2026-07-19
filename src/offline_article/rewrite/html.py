import logging
from collections.abc import Callable
from typing import Any

from bs4 import BeautifulSoup

from offline_article.discover.html import get_str_attr, normalize_url
from offline_article.rewrite.css import inline_css_urls

logger = logging.getLogger("offline-article.rewrite.html")


def inline_html_resources(
    html_content: str,
    base_url: str,
    fetch_text: Callable[[str], str | None],
    fetch_data_uri: Callable[[str], str | None],
) -> str:
    """
    Parses HTML and inlines stylesheets, scripts, images, and fonts into a self-contained page.
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Helper for CSS inline callback
    def css_inline_callback(url: str, is_css: bool) -> str | None:
        if is_css:
            return fetch_text(url)
        return fetch_data_uri(url)

    # 1. Inline Stylesheets (<link rel="stylesheet" href="...">)
    for link in soup.find_all("link"):
        rel: Any = link.get("rel") or []
        rel_list = rel if isinstance(rel, list) else [rel]
        rel_lower = [str(r).lower() for r in rel_list]

        if "stylesheet" in rel_lower:
            href = get_str_attr(link, "href")
            if href:
                abs_url = normalize_url(base_url, href)
                logger.info(f"Inlining stylesheet: {abs_url}")
                css_content = fetch_text(abs_url)
                if css_content is not None:
                    # Inline CSS nested urls first
                    inlined_css = inline_css_urls(css_content, abs_url, css_inline_callback)

                    # Create inline style tag
                    style_tag = soup.new_tag("style")
                    style_tag.string = inlined_css
                    link.replace_with(style_tag)

    # 2. Process inline <style> tags
    for style in soup.find_all("style"):
        if style.string:
            logger.debug("Inlining assets inside style tag")
            style.string = inline_css_urls(style.string, base_url, css_inline_callback)

    # 3. Inline Scripts (<script src="...">)
    for script in soup.find_all("script"):
        src = get_str_attr(script, "src")
        if src:
            abs_url = normalize_url(base_url, src)
            logger.info(f"Inlining script: {abs_url}")
            js_content = fetch_text(abs_url)
            if js_content is not None:
                # Replace with inline script content
                script_tag = soup.new_tag("script")
                # CDATA-like wrapping isn't strictly necessary but helpful if script contains HTML chars
                script_tag.string = js_content
                script.replace_with(script_tag)

    # 4. Inline Images
    for img in soup.find_all("img"):
        src = get_str_attr(img, "src")
        if src:
            abs_url = normalize_url(base_url, src)
            logger.debug(f"Inlining image src: {abs_url}")
            data_uri = fetch_data_uri(abs_url)
            if data_uri:
                img["src"] = data_uri

        # Handle srcset
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
                    data_uri = fetch_data_uri(abs_url)
                    if data_uri:
                        tokens[0] = data_uri
                    parts.append(" ".join(tokens))
            if parts:
                img["srcset"] = ", ".join(parts)

    # SVGs with image tags
    for svg_img in soup.find_all("image"):
        href_attr = "href" if svg_img.has_attr("href") else "xlink:href"
        href = get_str_attr(svg_img, href_attr)
        if href:
            abs_url = normalize_url(base_url, href)
            logger.debug(f"Inlining SVG image: {abs_url}")
            data_uri = fetch_data_uri(abs_url)
            if data_uri:
                svg_img[href_attr] = data_uri

    # Picture sources
    for source in soup.find_all("source"):
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
                    data_uri = fetch_data_uri(abs_url)
                    if data_uri:
                        tokens[0] = data_uri
                    parts.append(" ".join(tokens))
            if parts:
                source["srcset"] = ", ".join(parts)

        src = get_str_attr(source, "src")
        if src:
            abs_url = normalize_url(base_url, src)
            data_uri = fetch_data_uri(abs_url)
            if data_uri:
                source["src"] = data_uri

    # 5. Inline Metadata Assets (favicon and OpenGraph)
    icon_rels = {"icon", "shortcut", "apple-touch-icon"}
    for link in soup.find_all("link"):
        rel_val: Any = link.get("rel") or []
        rel_list = rel_val if isinstance(rel_val, list) else [rel_val]
        rel_lower = [str(r).lower() for r in rel_list]

        if any(any(icon in r for icon in icon_rels) for r in rel_lower):
            href = get_str_attr(link, "href")
            if href:
                abs_url = normalize_url(base_url, href)
                logger.debug(f"Inlining favicon link: {abs_url}")
                data_uri = fetch_data_uri(abs_url)
                if data_uri:
                    link["href"] = data_uri

    for meta in soup.find_all("meta"):
        property_attr = get_str_attr(meta, "property")
        name_attr = get_str_attr(meta, "name")
        content = get_str_attr(meta, "content")

        if content and (
            "image" in property_attr.lower() or "image" in name_attr.lower() or "icon" in name_attr.lower()
        ):
            abs_url = normalize_url(base_url, content)
            logger.debug(f"Inlining meta image content: {abs_url}")
            data_uri = fetch_data_uri(abs_url)
            if data_uri:
                meta["content"] = data_uri

    # 6. Inline Style Attributes (e.g. style="background-image: url(...)")
    for tag in soup.find_all(style=True):
        style_attr = get_str_attr(tag, "style")
        if style_attr:
            inlined_style = inline_css_urls(style_attr, base_url, css_inline_callback)
            tag["style"] = inlined_style

    # 7. Inline Iframes recursively
    for iframe in soup.find_all("iframe"):
        src = get_str_attr(iframe, "src")
        if src and not src.lower().startswith("data:"):
            abs_url = normalize_url(base_url, src)
            logger.info(f"Recursively inlining iframe: {abs_url}")
            iframe_html = fetch_text(abs_url)
            if iframe_html is not None:
                inlined_iframe = inline_html_resources(
                    iframe_html,
                    abs_url,
                    fetch_text=fetch_text,
                    fetch_data_uri=fetch_data_uri,
                )
                import base64

                encoded_iframe = base64.b64encode(inlined_iframe.encode("utf-8")).decode("utf-8")
                iframe["src"] = f"data:text/html;base64,{encoded_iframe}"

    return str(soup)
