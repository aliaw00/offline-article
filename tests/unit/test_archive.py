import zipfile
from pathlib import Path

from offline_article.archive.dir_writer import DirWriter
from offline_article.archive.factory import ArchiveWriterFactory
from offline_article.archive.html_writer import HtmlWriter
from offline_article.archive.zip_writer import ZipWriter


def test_archive_writer_factory() -> None:
    """Verifies that the factory returns the correct writer instance for each format."""
    assert isinstance(ArchiveWriterFactory.get_writer("html"), HtmlWriter)
    assert isinstance(ArchiveWriterFactory.get_writer("zip"), ZipWriter)
    assert isinstance(ArchiveWriterFactory.get_writer("dir"), DirWriter)


def test_html_writer(tmp_path: Path) -> None:
    """Verifies that HtmlWriter outputs a self-contained page with inlined resources."""
    html = "<html><body><img src='logo.png'></body></html>"
    assets = {"https://example.com/logo.png": (b"FAKE_IMAGE_BYTES", "image/png")}
    writer = HtmlWriter()
    out_file = tmp_path / "page.html"

    saved_path = writer.write(html, "https://example.com/", assets, out_file)

    assert saved_path == out_file
    assert out_file.is_file()

    content = out_file.read_text(encoding="utf-8")
    assert "data:image/png;base64," in content
    assert 'src="logo.png"' not in content


def test_dir_writer(tmp_path: Path) -> None:
    """Verifies that DirWriter outputs an index.html and assets/ folder with rewritten links."""
    html = "<html><body><img src='logo.png'></body></html>"
    assets = {"https://example.com/logo.png": (b"FAKE_IMAGE_BYTES", "image/png")}
    writer = DirWriter()
    out_dir = tmp_path / "extracted_dir"

    index_path = writer.write(html, "https://example.com/", assets, out_dir)

    assert index_path == out_dir / "index.html"
    assert index_path.is_file()
    assert (out_dir / "assets").is_dir()

    # Verify that there is a file inside assets/
    asset_files = list((out_dir / "assets").glob("*"))
    assert len(asset_files) == 1
    assert asset_files[0].name.startswith("logo_")

    # Verify index.html href rewriting
    index_content = index_path.read_text(encoding="utf-8")
    assert f"assets/{asset_files[0].name}" in index_content
    assert "logo.png" not in index_content


def test_zip_writer(tmp_path: Path) -> None:
    """Verifies that ZipWriter packages index.html and assets/ correctly into a ZIP file."""
    html = "<html><body><img src='logo.png'></body></html>"
    assets = {"https://example.com/logo.png": (b"FAKE_IMAGE_BYTES", "image/png")}
    writer = ZipWriter()
    out_zip = tmp_path / "archive.zip"

    saved_path = writer.write(html, "https://example.com/", assets, out_zip)

    assert saved_path == out_zip
    assert out_zip.is_file()
    assert zipfile.is_zipfile(out_zip)

    with zipfile.ZipFile(out_zip) as zf:
        namelist = zf.namelist()
        assert "index.html" in namelist
        assert any(name.startswith("assets/logo_") for name in namelist)
