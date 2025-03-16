import os
from dataclasses import dataclass, field

import dotenv

dotenv.load_dotenv()


@dataclass(frozen=True)
class Env:
    NOTION_API_KEY: str = field(init=False)
    NOTION_DATABASE_ID: str = field(init=False)
    NOTICE_WEBHOOK_HOST: str = field(init=False)
    NOTICE_WEBHOOK_PATH: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "NOTION_API_KEY", os.getenv("NOTION_API_KEY"))
        object.__setattr__(self, "NOTION_DATABASE_ID", os.getenv("DATABASE_ID"))
        object.__setattr__(
            self, "NOTICE_WEBHOOK_HOST", os.getenv("NOTICE_WEBHOOK_HOST")
        )
        object.__setattr__(
            self, "NOTICE_WEBHOOK_PATH", os.getenv("NOTICE_WEBHOOK_PATH")
        )
