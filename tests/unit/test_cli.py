from typer.testing import CliRunner

from offline_article.cli import app

runner = CliRunner()


def test_help() -> None:
    """Tests that the CLI help flag works correctly."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Save entire web pages for offline use." in result.stdout


def test_save_stub() -> None:
    """Tests that running save command invokes stub without errors."""
    result = runner.invoke(app, ["save", "https://example.com"])
    assert result.exit_code == 0
    assert "Starting capture for: https://example.com" in result.stdout
    assert "Success! Saved page to:" in result.stdout
