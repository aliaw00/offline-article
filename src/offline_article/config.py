from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "offline-article"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


class CaptureConfig(BaseModel):
    """
    Configuration for a single capture run.
    """
    format: str = Field(default="html", description="Output format (html, zip, dir, mhtml)")
    browser: str = Field(default="chromium", description="Browser to use (chromium, firefox, webkit)")
    profile_path: Path | None = Field(default=None, description="Path to browser profile directory")
    cookies_path: Path | None = Field(default=None, description="Path to cookies file (JSON or Netscape format)")
    wait_until: str = Field(default="networkidle", description="Wait condition (load, domcontentloaded, networkidle)")
    timeout: int = Field(default=30, description="Timeout in seconds for operations")
    scroll: bool = Field(default=False, description="Scroll down page to trigger lazy loading")
    proxy: str | None = Field(default=None, description="Proxy server URL (e.g. http://127.0.0.1:8080)")
    user_agent: str | None = Field(default=None, description="Custom User-Agent string")
    no_images: bool = Field(default=False, description="Disable loading images")
    no_js: bool = Field(default=False, description="Disable JavaScript execution")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    debug: bool = Field(default=False, description="Enable debug logging")
    keep_temp: bool = Field(default=False, description="Keep temporary files after execution")
    open_after_save: bool = Field(default=False, description="Open saved file in default browser after save")


class AppConfig(BaseModel):
    """
    Global application configuration.
    """
    default_capture_config: CaptureConfig = Field(default_factory=CaptureConfig)
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".cache" / "offline-article"
    )

    @classmethod
    def load_from_file(cls, path: Path = DEFAULT_CONFIG_FILE) -> "AppConfig":
        """Loads configuration from a JSON file, or returns default if file doesn't exist."""
        if not path.is_file():
            return cls()
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
            return cls.model_validate_json(content)
        except Exception:
            # Fallback to default config on parse errors
            return cls()

    def save_to_file(self, path: Path = DEFAULT_CONFIG_FILE) -> None:
        """Saves configuration to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
