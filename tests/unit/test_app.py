from pathlib import Path

from offline_article.app import App
from offline_article.config import CaptureConfig


def test_app_capture_example(local_server: str, tmp_path: Path) -> None:
    """Verifies that the App orchestrator successfully captures a page and inlines all assets."""
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

    # 1. Verify CSS from style.css & nested.css inlined and stylesheet link tag removed
    assert 'href="style.css"' not in content
    assert "color: blue;" in content
    assert "background-image: url('data:image/png;base64," in content

    # 2. Verify script.js inlined and script src tag removed
    assert 'src="script.js"' not in content
    assert "Hello from local test script" in content

    # 3. Verify logo.png inlined as data URI
    assert 'src="data:image/png;base64,' in content
    assert 'src="logo.png"' not in content
