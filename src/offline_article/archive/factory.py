from offline_article.archive.base import ArchiveWriter
from offline_article.archive.dir_writer import DirWriter
from offline_article.archive.html_writer import HtmlWriter
from offline_article.archive.zip_writer import ZipWriter
from offline_article.exceptions import ConfigurationError


class ArchiveWriterFactory:
    """Factory to retrieve the appropriate ArchiveWriter based on output format (Factory Pattern)."""

    @staticmethod
    def get_writer(format_name: str) -> ArchiveWriter:
        fmt = format_name.lower().strip()
        if fmt == "html":
            return HtmlWriter()
        elif fmt == "zip":
            return ZipWriter()
        elif fmt == "dir":
            return DirWriter()
        elif fmt == "mhtml":
            raise NotImplementedError("MHTML format support is not implemented yet.")
        else:
            raise ConfigurationError(f"Unsupported archive format: {format_name}")
