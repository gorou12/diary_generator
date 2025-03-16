import logging
from logging.handlers import RotatingFileHandler

from diary_generator.config.configuration import config

logger = logging.getLogger("internal")
logger.setLevel(logging.WARNING)

file_handler = RotatingFileHandler(
    f"{config.FILE_NAMES.LOG_DIR_NAME}logger.log",
    maxBytes=5 * 1024 * 1024,  # 1ファイル5MB
    backupCount=3,  # 3世代
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s"
)
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_format = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s"
)
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)


# ロガー内エラー用ロガー
def get_internal_logger():
    return logger
