import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "backend.log"

def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if any(
        isinstance(handler, TimedRotatingFileHandler)
        and Path(handler.baseFilename) == LOG_FILE
        for handler in root_logger.handlers
    ):
        return

    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        backupCount=14,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    ))
    root_logger.addHandler(handler)
