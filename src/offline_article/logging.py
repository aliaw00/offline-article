import logging
import sys

# We use standard library logging, but can format beautifully.
# If rich is installed, we can optionally use RichHandler.
try:
    from rich.logging import RichHandler

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(verbose: bool = False, debug: bool = False, log_file: str | None = None) -> None:
    """
    Configures logging for the offline-article package.

    If debug is True, log level is set to DEBUG.
    If verbose is True, log level is set to INFO.
    Otherwise, log level is set to WARNING.
    """
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    # Clear existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handlers: list[logging.Handler] = []

    # Terminal handler
    if HAS_RICH and sys.stderr.isatty():
        handlers.append(
            RichHandler(
                level=level,
                rich_tracebacks=True,
                show_time=False,
                omit_repeated_times=False,
            )
        )
    else:
        # Standard fallback formatter
        formatter = logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DATE_FORMAT)
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)
        stderr_handler.setLevel(level)
        handlers.append(stderr_handler)

    # File handler if specified
    if log_file:
        file_formatter = logging.Formatter(fmt=DEFAULT_FORMAT, datefmt=DATE_FORMAT)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)  # Always log debug to file if requested
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )

    # Set third-party logs to warning unless debug is active
    if not debug:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("playwright").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
