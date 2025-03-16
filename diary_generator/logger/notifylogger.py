import logging

from diary_generator.config.configuration import config
from diary_generator.logger.discord_handler import DiscordHandler

logger = logging.getLogger("diary-notify")
logger.setLevel(logging.INFO)

# Discord出力
discord_handler = DiscordHandler(config.ENV.NOTICE_WEBHOOK_URL)
discord_handler.setLevel(logging.INFO)
discord_format = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
discord_handler.setFormatter(discord_format)
logger.addHandler(discord_handler)


# 特別通知用ロガー
def get_logger():
    return logger
