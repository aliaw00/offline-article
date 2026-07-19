"""
Custom exception hierarchy for the offline-article tool.
"""


class OfflineArticleError(Exception):
    """Base exception for all offline-article errors."""

    pass


class ConfigurationError(OfflineArticleError):
    """Raised when configuration is invalid or missing."""

    pass


class BrowserError(OfflineArticleError):
    """Raised when browser automation (Playwright) fails."""

    pass


class RenderError(BrowserError):
    """Raised when rendering or stabilizing the page fails."""

    pass


class FetchError(OfflineArticleError):
    """Raised when downloading a page resource fails."""

    pass


class ParsingError(OfflineArticleError):
    """Raised when parsing HTML, CSS, or DOM elements fails."""

    pass


class ArchiveError(OfflineArticleError):
    """Raised when writing the archived content (HTML, ZIP, etc.) fails."""

    pass


class ValidationError(OfflineArticleError):
    """Raised when offline page validation fails."""

    pass
