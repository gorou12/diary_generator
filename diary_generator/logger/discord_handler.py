from logging import Handler

import requests

from diary_generator.logger import internallogger

log = internallogger.get_internal_logger()


class DiscordHandler(Handler):
    def __init__(self, webhook_url):
        super().__init__()
        self.webhook_url = webhook_url

    def emit(self, record):
        log_entry = self.format(record)
        try:
            requests.post(
                self.webhook_url,
                json={"content": log_entry},
                timeout=5,
            )
        except Exception as _:
            log.warning("⚠️ Discord通知失敗", stack_info=True)
