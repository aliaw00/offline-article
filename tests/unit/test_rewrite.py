from offline_article.rewrite.css import inline_css_urls
from offline_article.rewrite.html import inline_html_resources


def test_inline_css_urls() -> None:
    """Verifies that CSS assets and nested imports are correctly replaced by callbacks."""
    css = "@import 'imports.css';\nbody { background: url('logo.png'); }"

    def mock_fetch(url: str, is_css: bool) -> str | None:
        if is_css:
            return "h1 { color: red; }"
        return "DATA_URI"

    res = inline_css_urls(css, "https://example.com/", mock_fetch)
    assert "h1 { color: red; }" in res
    assert "background: url('DATA_URI')" in res


def test_inline_html_resources() -> None:
    """Verifies that HTML link, script, and image references are replaced with inlined contents."""
    html = (
        "<html>\n"
        "  <head>\n"
        '    <link rel="stylesheet" href="theme.css">\n'
        "  </head>\n"
        "  <body>\n"
        '    <script src="app.js"></script>\n'
        '    <img src="logo.png">\n'
        "  </body>\n"
        "</html>"
    )

    def mock_fetch_text(url: str) -> str | None:
        if "theme.css" in url:
            return "body { color: black; }"
        if "app.js" in url:
            return "console.log('inlined JS');"
        return None

    def mock_fetch_data_uri(url: str) -> str | None:
        if "logo.png" in url:
            return "DATA_URI_IMAGE"
        return None

    res = inline_html_resources(
        html,
        "https://example.com/",
        fetch_text=mock_fetch_text,
        fetch_data_uri=mock_fetch_data_uri,
    )

    # Assert stylesheet replaced by style tag containing CSS
    assert "<style>body { color: black; }</style>" in res
    assert 'href="theme.css"' not in res

    # Assert script tag has source replaced by content
    assert "<script>console.log('inlined JS');</script>" in res
    assert 'src="app.js"' not in res

    # Assert image src replaced by data URI
    assert 'src="DATA_URI_IMAGE"' in res
    assert 'src="logo.png"' not in res
