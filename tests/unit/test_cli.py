import zipfile
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


def test_save_command_zip(local_server: str, tmp_path: Path) -> None:
    """Tests that running the CLI save command with ZIP format successfully saves a zip archive."""
    output_file = tmp_path / "cli_saved.zip"
    result = runner.invoke(app, ["save", local_server, "--format", "zip", "--output", str(output_file)])
    assert result.exit_code == 0
    assert output_file.is_file()
    assert zipfile.is_zipfile(output_file)

    with zipfile.ZipFile(output_file) as zf:
        namelist = zf.namelist()
        assert "index.html" in namelist
        # Due to content-hash deduplication, identical logo.png and bg.png
        # may compile into a single file with either bg_ or logo_ prefix.
        assert any(name.startswith("assets/logo_") or name.startswith("assets/bg_") for name in namelist)


def test_save_command_dir(local_server: str, tmp_path: Path) -> None:
    """Tests that running the CLI save command with dir format successfully saves an offline folder."""
    output_dir = tmp_path / "cli_saved_dir"
    result = runner.invoke(app, ["save", local_server, "--format", "dir", "--output", str(output_dir)])
    assert result.exit_code == 0
    assert output_dir.is_dir()
    assert (output_dir / "index.html").is_file()
    assert (output_dir / "assets").is_dir()

    # Verify index.html content
    index_content = (output_dir / "index.html").read_text(encoding="utf-8")
    assert "Test Page" in index_content
