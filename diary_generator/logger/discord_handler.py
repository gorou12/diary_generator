from logging.handlers import HTTPHandler

from diary_generator.config.configuration import config


class DiscordHandler(HTTPHandler):
    def __init__(self):
        super().__init__(
            config.ENV.NOTICE_WEBHOOK_HOST,
            config.ENV.NOTICE_WEBHOOK_PATH,
            method="POST",
            secure=True,
        )

    def mapLogRecord(self, record):
        text = self.format(record)
        return {"content": text}
