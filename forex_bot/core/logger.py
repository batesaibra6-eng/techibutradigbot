"""
==============================================================================
CORE — Logging System
==============================================================================
Centralised rotating-file + console logger.
Every module obtains its logger via:
    from core.logger import get_logger
    logger = get_logger(__name__)
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from config.settings import LOG_DIR, LOG_LEVEL, LOG_MAX_BYTES, LOG_BACKUP_COUNT

os.makedirs(LOG_DIR, exist_ok=True)

_FMT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"

def _build_root_logger() -> logging.Logger:
    root = logging.getLogger("forex_bot")
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    if root.handlers:          # already configured
        return root

    # --- Console handler ---
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(_FMT, _DATE_FMT))
    root.addHandler(ch)

    # --- Rotating file handlers ---
    for name, path in [
        ("main",     os.path.join(LOG_DIR, "main.log")),
        ("trades",   os.path.join(LOG_DIR, "trades.log")),
        ("ai",       os.path.join(LOG_DIR, "ai.log")),
        ("errors",   os.path.join(LOG_DIR, "errors.log")),
    ]:
        fh = RotatingFileHandler(
            path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
        )
        fh.setFormatter(logging.Formatter(_FMT, _DATE_FMT))
        if name == "errors":
            fh.setLevel(logging.WARNING)
        root.addHandler(fh)

    return root


_root_logger = _build_root_logger()


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the forex_bot namespace."""
    return logging.getLogger(f"forex_bot.{name}")
