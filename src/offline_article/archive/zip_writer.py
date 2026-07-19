import logging
import tempfile
import zipfile
from pathlib import Path

from offline_article.archive.base import ArchiveWriter
from offline_article.archive.dir_writer import DirWriter
from offline_article.exceptions import ArchiveError

logger = logging.getLogger("offline-article.archive.zip")


class ZipWriter(ArchiveWriter):
    """Writes the page as a packaged ZIP archive containing index.html and assets/."""

    def write(
        self,
        html_content: str,
        base_url: str,
        assets: dict[str, tuple[bytes, str]],
        output_path: Path,
    ) -> Path:
        logger.info(f"Writing ZIP archive to: {output_path}")

        try:
            # 1. Use DirWriter to compile to a temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_dir_path = Path(tmpdir)
                dir_writer = DirWriter()

                # Write page to tmp directory
                dir_writer.write(html_content, base_url, assets, tmp_dir_path)

                # 2. Package the temporary directory into a ZIP archive
                if output_path.parent:
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in tmp_dir_path.rglob("*"):
                        if file_path.is_file():
                            # Store with relative path from tmpdir root
                            arcname = file_path.relative_to(tmp_dir_path)
                            zipf.write(file_path, arcname)

            return output_path
        except Exception as e:
            logger.error(f"Failed to write ZIP archive: {e}")
            raise ArchiveError(f"Failed to write ZIP archive: {e}") from e
