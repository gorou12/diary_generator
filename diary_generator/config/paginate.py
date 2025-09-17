from dataclasses import dataclass


@dataclass(frozen=True)
class Paginte:
    INDEX_TOPICS: int = 20
    TOPIC_LIST: int = 20
    DATE_LIST: int = 30
