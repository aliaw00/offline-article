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


def test_batch_command(local_server: str, tmp_path: Path) -> None:
    """Tests that running the CLI batch command captures all URLs in the input file."""
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text(f"{local_server}\n# this is a comment\n{local_server}\n", encoding="utf-8")

    output_dir = tmp_path / "batch_out"

    result = runner.invoke(app, ["batch", str(urls_file), "--output-dir", str(output_dir), "--format", "html", "--overwrite"])
    assert result.exit_code == 0
    assert "Successfully captured 2/2 pages" in result.stdout

    # Check that output files exist
    saved_files = list(output_dir.glob("*.html"))
    assert len(saved_files) >= 1


def test_validate_command(local_server: str, tmp_path: Path) -> None:
    """Tests that running the CLI validate command checks archives correctly."""
    # 1. Capture a healthy single-file HTML page
    output_file = tmp_path / "healthy.html"
    result_save = runner.invoke(app, ["save", local_server, "--output", str(output_file)])
    assert result_save.exit_code == 0

    # Validate the healthy page
    result_val = runner.invoke(app, ["validate", str(output_file)])
    assert result_val.exit_code == 0
    assert "Offline archive is healthy" in result_val.stdout

    # 2. Try validating a non-existent path
    result_bad = runner.invoke(app, ["validate", str(tmp_path / "does_not_exist.html")])
    assert result_bad.exit_code != 0
    assert "Path does not exist" in result_bad.stdout


def test_version_flag() -> None:
    """Tests that the CLI version flag works correctly."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "offline-article version" in result.stdout
    assert "1.1.1" in result.stdout


def test_version_short_flag() -> None:
    """Tests that the CLI -V short flag works correctly."""
    result = runner.invoke(app, ["-V"])
    assert result.exit_code == 0
    assert "offline-article version" in result.stdout


def test_help_contains_version_option() -> None:
    """Tests that help page shows the version option."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--version" in result.stdout or "-V" in result.stdout


def test_update_command_help() -> None:
    """Tests that the update command help works."""
    result = runner.invoke(app, ["update", "--help"])
    assert result.exit_code == 0
    assert "Update offline-article" in result.stdout


def test_update_command_execution() -> None:
    """Tests that the update command executes without error."""
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    # Should either be up to date or show update output
    assert "Checking for updates" in result.stdout or "Update" in result.stdout


def test_save_with_invalid_format(local_server: str, tmp_path: Path) -> None:
    """Tests that save command rejects invalid format."""
    output_file = tmp_path / "invalid.html"
    result = runner.invoke(app, ["save", local_server, "--format", "invalid_format", "--output", str(output_file)])
    # Should fail due to invalid format
    assert result.exit_code != 0


def test_save_nonexistent_url(tmp_path: Path) -> None:
    """Tests that save command handles nonexistent URL gracefully."""
    output_file = tmp_path / "should_fail.html"
    result = runner.invoke(app, ["save", "http://nonexistent.invalid/page", "--output", str(output_file), "--timeout", "5"])
    # Should fail since URL doesn't exist
    assert result.exit_code != 0


def test_batch_empty_file(tmp_path: Path) -> None:
    """Tests batch command with empty file."""
    urls_file = tmp_path / "empty.txt"
    urls_file.write_text("", encoding="utf-8")
    
    output_dir = tmp_path / "batch_out"
    result = runner.invoke(app, ["batch", str(urls_file), "--output-dir", str(output_dir)])
    assert result.exit_code == 0
    assert "No valid URLs found" in result.stdout


def test_batch_comments_only_file(tmp_path: Path) -> None:
    """Tests batch command with file containing only comments."""
    urls_file = tmp_path / "comments.txt"
    urls_file.write_text("# comment 1\n# comment 2\n", encoding="utf-8")
    
    output_dir = tmp_path / "batch_out"
    result = runner.invoke(app, ["batch", str(urls_file), "--output-dir", str(output_dir)])
    assert result.exit_code == 0
    assert "No valid URLs found" in result.stdout


def test_validate_unsupported_extension(tmp_path: Path) -> None:
    """Tests validate command with unsupported file extension."""
    fake_file = tmp_path / "unsupported.txt"
    fake_file.write_text("dummy content", encoding="utf-8")
    
    result = runner.invoke(app, ["validate", str(fake_file)])
    assert result.exit_code != 0
    assert "Unsupported file extension" in result.stdout
