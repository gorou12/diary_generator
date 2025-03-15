from dataclasses import dataclass


@dataclass(frozen=True)
class Paginte:
    INDEX: int = 10
    TOPIC_LIST: int = 20
    DATE_LIST: int = 30
