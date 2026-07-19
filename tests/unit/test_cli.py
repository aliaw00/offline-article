from pathlib import Path

from typer.testing import CliRunner

from offline_article.cli import app

runner = CliRunner()


def test_help() -> None:
    """Tests that the CLI help flag works correctly."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Save entire web pages for offline use." in result.stdout


def test_save_command(local_server: str, tmp_path: Path) -> None:
    """Tests that running the CLI save command successfully saves a page."""
    output_file = tmp_path / "cli_saved.html"
    result = runner.invoke(app, ["save", local_server, "--output", str(output_file)])
    assert result.exit_code == 0
    assert f"Starting capture for: {local_server}" in result.stdout
    assert "Success! Saved page to:" in result.stdout
    assert output_file.is_file()

    with open(output_file, encoding="utf-8") as f:
        content = f.read()
    assert "Test Page" in content
