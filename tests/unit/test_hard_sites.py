import base64
from unittest.mock import MagicMock

from offline_article.app import serialize_page_dom
from offline_article.rewrite.html import inline_html_resources


def test_shadow_dom_serialization() -> None:
    """Tests that serialize_page_dom correctly evaluates and returns serialized Declarative Shadow DOM HTML."""
    page = MagicMock()
    serialized_html = (
        "<html><body>"
        '<my-component><template shadowrootmode="open"><span>shadow text</span></template></my-component>'
        "</body></html>"
    )
    # Mock evaluate returning the serialized string
    page.evaluate.return_value = serialized_html

    res = serialize_page_dom(page)

    assert '<template shadowrootmode="open">' in res
    assert "<span>shadow text</span>" in res
    assert res.startswith("<!DOCTYPE html>")


def test_shadow_dom_serialization_fallback() -> None:
    """Tests that serialize_page_dom falls back to page.content() if evaluate throws an error."""
    page = MagicMock()
    page.evaluate.side_effect = Exception("JS evaluation failed")
    page.content.return_value = "<html><body>Fallback Content</body></html>"

    res = serialize_page_dom(page)

    assert "Fallback Content" in res
    assert "shadowrootmode" not in res


def test_inline_iframe_recursive() -> None:
    """Tests that inline_html_resources recursively inlines iframes using base64 data URIs."""
    html = '<html><body><iframe src="nested_frame.html"></iframe></body></html>'

    def mock_fetch_text(url: str) -> str | None:
        if "nested_frame.html" in url:
            return "<html><body><h1>Hello Iframe</h1></body></html>"
        return None

    def mock_fetch_data_uri(url: str) -> str | None:
        return None

    res = inline_html_resources(
        html,
        "https://example.com/",
        fetch_text=mock_fetch_text,
        fetch_data_uri=mock_fetch_data_uri,
    )

    # Assert src was rewritten to a base64 text/html data URI
    assert 'src="data:text/html;base64,' in res
    assert "nested_frame.html" not in res

    # Decode the base64 content to verify it contains the iframe's HTML
    base64_part = res.split('src="data:text/html;base64,')[1].split('"')[0]
    decoded_html = base64.b64decode(base64_part).decode("utf-8")
    assert "<h1>Hello Iframe</h1>" in decoded_html
