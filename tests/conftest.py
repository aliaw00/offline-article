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
    """Spins up a local HTTP server serving static HTML content for E2E tests."""
    # Find a free port dynamically
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create a sample index.html
        index_file = tmp_path / "index.html"
        index_file.write_text(
            "<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>", encoding="utf-8"
        )

        # Create a subpage.html to test relative navigation
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
