import email
from pathlib import Path

from offline_article.archive.mhtml_writer import MhtmlWriter


def test_mhtml_writer(tmp_path: Path) -> None:
    """Tests that MhtmlWriter successfully saves a page and its assets in RFC 2557 MHTML format."""
    html_content = (
        "<html>\n"
        "  <head>\n"
        '    <link rel="stylesheet" href="style.css">\n'
        "  </head>\n"
        "  <body>\n"
        "    <h1>MHTML Test</h1>\n"
        '    <img src="logo.png">\n'
        "  </body>\n"
        "</html>"
    )
    url = "https://example.com/"
    assets = {
        "https://example.com/style.css": (b"body { color: blue; }", "text/css"),
        "https://example.com/logo.png": (b"PNG_BYTES", "image/png"),
    }
    output_file = tmp_path / "saved.mhtml"

    writer = MhtmlWriter()
    saved_path = writer.write(html_content, url, assets, output_file)

    assert saved_path == output_file
    assert output_file.is_file()

    # Parse MHTML back using Python's standard email parser
    with open(output_file, "rb") as f:
        msg = email.message_from_binary_file(f)

    # Verify overall headers
    assert msg.is_multipart()
    assert msg["Snapshot-Content-Location"] == url
    assert msg.get_content_type() == "multipart/related"

    # Verify sub-parts
    parts = list(msg.walk())

    # Filter out the container part
    subparts = [p for p in parts if p.get_content_type() != "multipart/related"]
    assert len(subparts) == 3

    # 1. Main HTML part
    html_part = subparts[0]
    assert html_part.get_content_type() == "text/html"
    assert html_part["Content-Location"] == url
    html_decoded = html_part.get_payload(decode=True).decode("utf-8")
    assert "https://example.com/style.css" in html_decoded
    assert "https://example.com/logo.png" in html_decoded

    # 2. Style part
    css_part = next(p for p in subparts if p.get_content_type() == "text/css")
    assert css_part["Content-Location"] == "https://example.com/style.css"
    assert css_part.get_payload(decode=True) == b"body { color: blue; }"

    # 3. Logo part
    img_part = next(p for p in subparts if p.get_content_type() == "image/png")
    assert img_part["Content-Location"] == "https://example.com/logo.png"
    assert img_part.get_payload(decode=True) == b"PNG_BYTES"
