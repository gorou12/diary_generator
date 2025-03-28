import logging
from logging.handlers import RotatingFileHandler

from diary_generator.config.configuration import config
from diary_generator.logger.discord_handler import DiscordHandler

logger = logging.getLogger("diary_system")
logger.setLevel(logging.DEBUG)

# ファイル出力
file_handler = RotatingFileHandler(
    f"{config.FILE_NAMES.LOG_DIR_NAME}system.log",
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

# コンソール出力
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_format = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s"
)
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

# Discord出力
discord_handler = DiscordHandler(config.ENV.NOTICE_WEBHOOK_URL)
discord_handler.setLevel(logging.WARN)
discord_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
discord_handler.setFormatter(discord_format)
logger.addHandler(discord_handler)


# ふつうのロガー
def get_logger():
    return logger
