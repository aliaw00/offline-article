from dataclasses import dataclass, field
from typing import Any


@dataclass
class Resource:
    """Represents a discovered and retrieved web page asset (image, stylesheet, script, font, etc.)."""
    url: str
    content_type: str
    content: bytes
    sha256: str
    local_path: str | None = None
    inlined_data_uri: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
