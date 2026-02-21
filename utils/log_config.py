"""
Centralised logging configuration for RadBot.

All logs are written to the logs/ directory with automatic rotation:
  - radbot.log        : Full application log (DEBUG+), rotated at 5MB, 10 backups
  - error.log         : Errors and critical only (ERROR+), rotated at 2MB, 5 backups
  - trades.log        : All trade activity (INFO+), rotated at 2MB, 5 backups
  - failed_trades.log : Failed trades only (WARNING+), rotated at 2MB, 5 backups
  - api_usage.log     : API call rate summaries (INFO+), rotated at ~20KB, 1 backup (~1h history)
  - crash.log         : Unhandled exception reports (appended)
  - fatal_crash.log   : faulthandler output for segfaults (appended)

Console output is filtered to INFO+ to keep terminal readable.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path

from config.paths import LOGS_DIR


def _ensure_logs_dir():
    """Create the logs directory if it doesn't exist."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _rotating_handler(filename, max_bytes, backup_count, level, formatter):
    """Helper to create a configured RotatingFileHandler."""
    handler = logging.handlers.RotatingFileHandler(
        filename=LOGS_DIR / filename,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def setup_logging(console_level=logging.INFO, file_level=logging.DEBUG):
    """
    Configure application-wide logging with rotation.

    Args:
        console_level: Minimum level for console output (default INFO).
        file_level:    Minimum level for the main log file (default DEBUG).
    """
    _ensure_logs_dir()

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # ── Main application log (DEBUG+, 5 MB × 10 backups) ──
    main_handler = _rotating_handler("radbot.log", 5 * 1024 * 1024, 10, file_level, formatter)

    # ── Error-only log (ERROR+, 2 MB × 5 backups) ──
    error_handler = _rotating_handler("error.log", 2 * 1024 * 1024, 5, logging.ERROR, formatter)

    # ── Console handler (INFO+ by default) ──
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)

    # ── Apply to root logger ──
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove any pre-existing handlers (e.g. from basicConfig)
    root_logger.handlers.clear()

    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)

    # ── Trade activity log (INFO+, 2 MB × 5 backups) ──
    # Named logger: lines propagate to root (radbot.log) AND write to trades.log
    trades_handler = _rotating_handler("trades.log", 2 * 1024 * 1024, 5, logging.INFO, formatter)
    trades_logger = logging.getLogger('radbot.trades')
    trades_logger.addHandler(trades_handler)

    # ── Failed trades log (WARNING+, 2 MB × 5 backups) ──
    failed_trades_handler = _rotating_handler("failed_trades.log", 2 * 1024 * 1024, 5, logging.WARNING, formatter)
    trades_logger.addHandler(failed_trades_handler)

    # ── API usage log (INFO+, ~20 KB × 1 backup ≈ 1 hour of history) ──
    # Session totals & uptime are in every line, so older entries aren't needed.
    api_handler = _rotating_handler("api_usage.log", 20 * 1024, 1, logging.INFO, formatter)
    api_logger = logging.getLogger('radbot.api_usage')
    api_logger.addHandler(api_handler)

    # Quieten noisy third-party loggers
    for noisy in ("urllib3", "PIL", "matplotlib", "PySide6", "aiohttp"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_crash_log_path() -> Path:
    """Return the path to the crash report log (for unhandled exceptions)."""
    _ensure_logs_dir()
    return LOGS_DIR / "crash.log"


def get_faulthandler_path() -> Path:
    """Return the path for faulthandler output (segfaults / fatal errors)."""
    _ensure_logs_dir()
    return LOGS_DIR / "fatal_crash.log"
