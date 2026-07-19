from abc import ABC, abstractmethod
from pathlib import Path


class ArchiveWriter(ABC):
    """Base interface for all output archive writers (Strategy Pattern)."""

    @abstractmethod
    def write(
        self,
        html_content: str,
        base_url: str,
        assets: dict[str, tuple[bytes, str]],
        output_path: Path,
    ) -> Path:
        """
        Writes the HTML page and its associated assets to the destination.

        :param html_content: The raw HTML content of the page.
        :param base_url: The base URL of the captured page.
        :param assets: Dictionary mapping absolute asset URL to (content_bytes, content_type).
        :param output_path: Target path for the output.
        :return: Path to the generated archive/file.
        """
        pass
