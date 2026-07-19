from offline_article.config import AppConfig, CaptureConfig


def test_default_capture_config() -> None:
    """Verifies default values of CaptureConfig."""
    config = CaptureConfig()
    assert config.format == "html"
    assert config.browser == "chromium"
    assert config.wait_until == "networkidle"
    assert config.timeout == 30
    assert config.scroll is False


def test_app_config_defaults() -> None:
    """Verifies default values of AppConfig."""
    app_config = AppConfig()
    assert app_config.default_capture_config.format == "html"
    assert "offline-article" in str(app_config.cache_dir)
