from offline_article.discover.css import discover_css_resources
from offline_article.discover.html import discover_html_resources, normalize_url


def test_normalize_url() -> None:
    """Verifies that URLs are correctly normalized (made absolute and stripped of fragments)."""
    base = "https://example.com/sub/dir/page.html"
    assert normalize_url(base, "style.css") == "https://example.com/sub/dir/style.css"
    assert normalize_url(base, "/images/pic.png") == "https://example.com/images/pic.png"
    assert normalize_url(base, "https://google.com/icon.ico#test") == "https://google.com/icon.ico"
    assert normalize_url(base, "  /trimmed.js  ") == "https://example.com/trimmed.js"


def test_discover_html_resources() -> None:
    """Verifies discovery of stylesheets, scripts, images, iframes, and metadata in HTML."""
    html = """
    <html>
      <head>
        <title>Test Discovery</title>
        <link rel="stylesheet" href="theme.css">
        <link rel="icon" href="/favicon.ico">
        <meta property="og:image" content="https://example.com/banner.jpg">
      </head>
      <body>
        <script src="app.js"></script>
        <img src="logo.png" srcset="logo-2x.png 2x, logo-3x.png 3x">
        <picture>
          <source srcset="image.webp" type="image/webp">
          <img src="image.jpg" alt="Fallback">
        </picture>
        <iframe src="embed.html"></iframe>
      </body>
    </html>
    """
    base = "https://example.com/index.html"
    res = discover_html_resources(html, base)

    assert res["stylesheets"] == {"https://example.com/theme.css"}
    assert res["scripts"] == {"https://example.com/app.js"}
    assert res["images"] == {
        "https://example.com/logo.png",
        "https://example.com/logo-2x.png",
        "https://example.com/logo-3x.png",
        "https://example.com/image.webp",
        "https://example.com/image.jpg",
    }
    assert res["iframes"] == {"https://example.com/embed.html"}
    assert res["metadata"] == {"https://example.com/favicon.ico", "https://example.com/banner.jpg"}


def test_discover_css_resources() -> None:
    """Verifies discovery of imports, background images, and fonts in CSS."""
    css = """
    @import "imports.css";
    @import url("theme.css");

    body {
        background-image: url('bg.png');
        cursor: url(custom.cur), pointer;
    }
    @font-face {
        font-family: 'Open Sans';
        src: url('fonts/opensans.woff2') format('woff2');
    }
    """
    base = "https://example.com/css/main.css"
    res = discover_css_resources(css, base)

    assert res["stylesheets"] == {"https://example.com/css/imports.css", "https://example.com/css/theme.css"}
    assert res["images"] == {"https://example.com/css/bg.png", "https://example.com/css/custom.cur"}
    assert res["fonts"] == {"https://example.com/css/fonts/opensans.woff2"}
