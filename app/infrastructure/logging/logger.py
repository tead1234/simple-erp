import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def _setup_logger() -> logging.Logger:
    log = logging.getLogger("erp")
    log.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "ERROR")))
    try:
        Path("logs").mkdir(exist_ok=True)
        handler = TimedRotatingFileHandler(
            "logs/erp.log", when="midnight", backupCount=7, encoding="utf-8"
        )
    except OSError:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
    return log


logger = _setup_logger()
