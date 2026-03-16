"""Настройка логгера приложения. Отдельный модуль в корне, чтобы config не тянул за собой core."""
import json
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "3"))

os.makedirs(LOG_DIR, exist_ok=True)


def _utc_iso_timestamp(record: logging.LogRecord) -> str:
    from time import gmtime

    t = gmtime(record.created)
    ms = int((record.created % 1) * 1000)
    return f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}T{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}.{ms:03d}Z"


class StructuredJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": _utc_iso_timestamp(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


_formatter = StructuredJsonFormatter()


def _file_handler(path: str, level: int = logging.NOTSET) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    handler.setLevel(level)
    handler.setFormatter(_formatter)
    return handler


logger = logging.getLogger("backend")
logger.setLevel(logging.INFO)
logger.propagate = False
logger.addHandler(_file_handler(f"{LOG_DIR}/all_logs.log"))
logger.addHandler(_file_handler(f"{LOG_DIR}/errors.log", level=logging.ERROR))
_console = logging.StreamHandler()
_console.setFormatter(_formatter)
logger.addHandler(_console)
