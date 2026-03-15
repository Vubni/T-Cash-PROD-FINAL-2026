import os

from logging_setup import logger

DATE_BASE_CONNECT = {
    "host": os.getenv("DB_IP"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_DB"),
}

SECRET = os.getenv("RANDOM_SECRET", "AJd27GqoS#gvxp@V")

CALC_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8008")

CATEGORIES_CONFIG_PATH = os.getenv(
    "CATEGORIES_CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "config", "categories_config.json"),
)
ALL_CATEGORIES_DEFAULT = 0
DEFAULT_MAX_SELECTION_COUNT = 5

