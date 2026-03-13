from dotenv import load_dotenv
import os, json
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()

API_KEY = os.getenv("API_KEY")

EMAIL_HOSTNAME = os.getenv("EMAIL_HOSTNAME")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

DATE_BASE_CONNECT = {"host": os.getenv("DB_IP"), 
             "user": os.getenv("DB_USER"), 
             "password": os.getenv("DB_PASSWORD"), 
             "database": os.getenv("DB_DB")}

SECRET = os.getenv("RANDOM_SECRET", "AJd27GqoS#gvxp@V")


bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode=ParseMode.HTML))


LOG_DIR = "logs"
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 3

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

import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("backend")
logger.setLevel(logging.INFO)
logger.propagate = False

_formatter = StructuredJsonFormatter()


def _file_handler(path: str, level: int = logging.NOTSET) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    handler.setLevel(level)
    handler.setFormatter(_formatter)
    return handler


logger.addHandler(_file_handler(f"{LOG_DIR}/all_logs.log"))
logger.addHandler(_file_handler(f"{LOG_DIR}/errors.log", level=logging.ERROR))

_console = logging.StreamHandler()
_console.setFormatter(_formatter)
logger.addHandler(_console)
