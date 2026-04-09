"""
Application logging configuration.
"""

import logging
import os
import sys

_RESET = "\033[0m"
_BOLD = "\033[1m"

_LEVEL_COLOURS: dict[int, str] = {
    logging.DEBUG: "\033[36m",  # cyan
    logging.INFO: "\033[32m",  # green
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[35m",  # magenta
}


class _ColourFormatter(logging.Formatter):
    """Logging formatter that applies ANSI colour codes to the level name.

    Colour is only applied when the attached stream is a TTY to avoid
    polluting piped output or log aggregators with escape sequences.
    """

    def __init__(self, use_colour: bool = True) -> None:
        super().__init__(
            fmt="[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self._use_colour = use_colour

    def formatMessage(self, record: logging.LogRecord) -> str:
        """Format the log record, colouring the level name when enabled."""
        if self._use_colour:
            colour = _LEVEL_COLOURS.get(record.levelno, "")
            record.levelname = f"{_BOLD}{colour}{record.levelname}{_RESET}"
        return super().formatMessage(record)


def get_logger(name: str | None = None, log_level: str | int | None = None) -> logging.Logger:
    """Create or retrieve a named logger with a coloured stdout handler.

    Uses Python's logging hierarchy: calling this function with the same ``name``
    returns the existing logger instance. Handlers are only attached once to avoid
    duplicate log output across multiple calls.

    Colour output is enabled automatically when stdout is a TTY and disabled
    otherwise (e.g. in CI pipelines or Cloud Run log aggregation).

    Args:
        name: Logger name, typically ``__name__`` of the calling module.
            Defaults to the root logger when ``None``.
        log_level: Desired log level. Accepts a logging constant (e.g.
            ``logging.DEBUG``), a case-insensitive string (e.g. ``"debug"``),
            or ``None`` to default to ``INFO``.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    if log_level is None:
        logger.setLevel(logging.INFO)
    elif isinstance(log_level, str):
        level = logging.getLevelNamesMapping().get(log_level.upper(), logging.INFO)
        logger.setLevel(level)
    else:
        logger.setLevel(log_level)

    if not logger.handlers:
        use_colour = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(_ColourFormatter(use_colour=use_colour))
        logger.addHandler(console_handler)

    return logger


app_env = os.environ.get("APP_ENV", "local")
logger = get_logger(log_level=logging.DEBUG if app_env == "local" else logging.INFO)
