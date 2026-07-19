from pathlib import Path

from offline_article.app import App
from offline_article.config import CaptureConfig


def test_app_capture_example(local_server: str, tmp_path: Path) -> None:
    """Verifies that the App orchestrator successfully captures a page from the local server and writes it to disk."""
    config = CaptureConfig()
    app = App(config)
    output_file = tmp_path / "example.html"

    saved_path = app.run(local_server, output_file)

    assert saved_path == output_file
    assert output_file.is_file()

    with open(output_file, encoding="utf-8") as f:
        content = f.read()

    assert "<html" in content.lower()
    assert "Test Page" in content
    assert "Hello World" in content
