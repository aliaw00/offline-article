import base64
import http.server
import socket
import tempfile
import threading
from collections.abc import Generator
from pathlib import Path

import pytest


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Simple HTTP request handler that suppresses default logging to stderr."""

    def log_message(self, format: str, *args: list) -> None:
        pass


@pytest.fixture(scope="session")
def local_server() -> Generator[str, None, None]:
    """Spins up a local HTTP server serving HTML, CSS, JS, and image assets for E2E tests."""
    # Find a free port dynamically
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Create a sample index.html linking stylesheets, images, scripts
        index_file = tmp_path / "index.html"
        index_file.write_text(
            "<html>\n"
            "  <head>\n"
            "    <title>Test Page</title>\n"
            '    <link rel="stylesheet" href="style.css">\n'
            "  </head>\n"
            "  <body>\n"
            "    <h1>Hello World</h1>\n"
            '    <img id="logo" src="logo.png">\n'
            '    <script src="script.js"></script>\n'
            "  </body>\n"
            "</html>",
            encoding="utf-8",
        )

        # 2. Create style.css with an @import and background-image url()
        style_file = tmp_path / "style.css"
        style_file.write_text(
            '@import "nested.css";\nbody {\n    background-image: url("bg.png");\n}', encoding="utf-8"
        )

        # 3. Create nested.css
        nested_file = tmp_path / "nested.css"
        nested_file.write_text("h1 {\n    color: blue;\n}", encoding="utf-8")

        # 4. Create script.js
        script_file = tmp_path / "script.js"
        script_file.write_text("console.log('Hello from local test script');", encoding="utf-8")

        # 5. Create 1x1 transparent PNG files for logo.png and bg.png
        base64_str = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        png_bytes = base64.b64decode(base64_str)

        with open(tmp_path / "logo.png", "wb") as f:
            f.write(png_bytes)

        with open(tmp_path / "bg.png", "wb") as f:
            f.write(png_bytes)

        # 6. Create subpage.html
        subpage_file = tmp_path / "subpage.html"
        subpage_file.write_text(
            "<html><head><title>Subpage</title></head><body><h1>Subpage content</h1></body></html>", encoding="utf-8"
        )

        class CustomHandler(QuietHandler):
            def __init__(self, *args: list, **kwargs: dict) -> None:
                super().__init__(*args, directory=tmpdir, **kwargs)

        server = http.server.HTTPServer(("127.0.0.1", port), CustomHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        yield f"http://127.0.0.1:{port}"

        server.shutdown()
        server.server_close()
