"""Logging integration for Ornata.

Provides `OrnataHandler`, a logging.Handler subclass that formats messages
with timestamps, levels, logger name, and optional colorization using
Ornata's Color. Also provides basic file logging with simple rotation.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TextIO

_logging_initialized = False

# Keep constants for logging here because logging is used EVERYWHERE and causes a bunch of circular issues
LOGGING_ENABLED: bool = True
LOG_TO_CONSOLE: bool = False  # Default: only log to file to keep terminal clean
LOG_TO_FILE: bool = True

LOG_LEVEL_COLORS = {
    logging.DEBUG: "#00FFFF",
    logging.INFO: "#00FF00",
    logging.WARNING: "#FFFF00",
    logging.ERROR: "#FF0000",
    logging.CRITICAL: "#FF0000"
}

LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "ornata.log"
LOG_ROTATION_COUNT = 3


def _get_disabled_logger(logger_name: str) -> logging.Logger:
    """Return a logger that swallows all records when logging is disabled.

    Parameters
    ----------
    logger_name : str
        Name of the logger to disable.

    Returns
    -------
    logging.Logger
        Logger instance configured to drop all log records.
    """
    logger = logging.getLogger(logger_name)
    if not any(isinstance(handler, logging.NullHandler) for handler in logger.handlers):
        logger.addHandler(logging.NullHandler())
    logger.disabled = True
    logger.propagate = False
    return logger


def _get_project_root() -> Path:
    """Return the project root directory path.

    Returns
    -------
    Path
        The resolved project root directory.
    """
    return Path(__file__).resolve().parents[3]


def _ensure_log_directory() -> Path:
    """Ensure that the logs directory exists and return its path.

    Returns
    -------
    Path
        The path to the logs directory.
    """
    root = _get_project_root()
    log_dir = root / LOG_DIR_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _rotate_log_files(base_path: Path) -> None:
    """Rotate log files up to the configured rotation count.

    Parameters
    ----------
    base_path : Path
        The base path of the active log file (ornata.log).
    """
    for index in range(LOG_ROTATION_COUNT, 0, -1):
        suffix = "" if index == 1 else f"_{index - 1}"
        source = base_path.with_name(f"{base_path.stem}{suffix}{base_path.suffix}")
        target = base_path.with_name(f"{base_path.stem}_{index}{base_path.suffix}")
        if source.exists():
            try:
                source.rename(target)
            except OSError:
                continue

def hex_to_ansi(hex_color: str) -> str:
    """Return the ANSI escape sequence for a #RRGGBB colour."""
    rgb = hex_to_rgb(hex_color)
    return rgb_to_ansi(rgb) if rgb else ""

def rgb_to_ansi(rgb: tuple[int, int, int]) -> str:
    """Return the ANSI escape sequence for a 24-bit RGB color."""
    r, g, b = rgb
    r = 0 if r < 0 else (255 if r > 255 else int(r))
    g = 0 if g < 0 else (255 if g > 255 else int(g))
    b = 0 if b < 0 else (255 if b > 255 else int(b))
    return f"\033[38;2;{r};{g};{b}m"

def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Convert a #RRGGBB string to an RGB tuple."""
    s = hex_color.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        return None
    try:
        v = int(s, 16)
    except ValueError:
        return None
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)

class OrnataFormatter(logging.Formatter):
    """Formatter that applies color by level and rich metadata."""

    def format(self, record: logging.LogRecord) -> str:
        hex_color = LOG_LEVEL_COLORS.get(record.levelno)
        ansi_color = hex_to_ansi(hex_color) if hex_color else ""
        level = logging.getLevelName(record.levelno)
        time = self.formatTime(record, self.datefmt)
        msg = super().format(record)
        location = f"{record.filename}:{record.lineno}"
        reset = "\033[0m" if ansi_color else ""
        return f"{ansi_color}[{time}] | {level:>2} | {location} | {msg}{reset}"


class OrnataHandler(logging.StreamHandler[TextIO]):
    """Logging handler that outputs ANSI-colored logs compatible with Ornata."""

    def __init__(self, stream: TextIO | None = None) -> None:
        super().__init__(stream)
        fmt = OrnataFormatter("%(name)s | %(message)s", datefmt="%H:%M:%S")
        self.setFormatter(fmt)


def _initialize_root_logging() -> None:
    """Initialize root logging with console and file handlers.

    This function is idempotent and safe to call multiple times.
    Controlled by LOGGING_ENABLED, LOG_TO_CONSOLE, and LOG_TO_FILE flags.
    """
    global _logging_initialized

    if _logging_initialized:
        return

    if not LOGGING_ENABLED:
        _logging_initialized = True
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Console handler (conditional)
    if LOG_TO_CONSOLE:
        if not any(isinstance(h, OrnataHandler) for h in root_logger.handlers):
            root_logger.addHandler(OrnataHandler())

    # File handler (conditional)
    if LOG_TO_FILE:
        log_dir = _ensure_log_directory()
        log_path = log_dir / LOG_FILE_NAME

        if log_path.exists():
            _rotate_log_files(log_path)

        file_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)8s %(name)s:%(lineno)d - %(message)s",
            datefmt="%H:%M:%S",
        )
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    _logging_initialized = True


def get_logger(
    name: str = "ornata",
    level: int = logging.DEBUG,
    __name__: str | None = None,
) -> logging.Logger:
    """Create or fetch a logger preconfigured with Ornata handlers.

    Parameters
    ----------
    name : str, optional
        The logger name to retrieve.
    __name__ : str | None, optional
        Alias for :pyparam:`name` for backwards compatibility with ``__name__``
        keyword arguments.
    level : int, optional
        The logging level to apply to the logger.

    Returns
    -------
    logging.Logger
        The configured logger instance.
    """
    logger_name = __name__ if __name__ is not None else name
    if not LOGGING_ENABLED:
        return _get_disabled_logger(logger_name)

    _initialize_root_logging()
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    return logger
