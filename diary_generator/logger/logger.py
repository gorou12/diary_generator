import logging
from logging.handlers import RotatingFileHandler

from diary_generator.logger.discord_handler import DiscordHandler
from diary_generator.config.configuration import config

# 共通Logger
logger = logging.getLogger("diary_system")
logger.setLevel(logging.DEBUG)  # INFOレベル以上を記録

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

# 必要なら、ここでチャット送信用のカスタムHandlerも作れる（後述）
discord_handler = DiscordHandler()
discord_handler.setLevel(logging.WARN)
discord_format = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s"
)
discord_handler.setFormatter(discord_format)
logger.addHandler(discord_handler)


# 外部から import して使う
def get_logger():
    return logger
