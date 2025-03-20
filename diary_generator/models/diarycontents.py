from dataclasses import dataclass, field
from enum import Enum, auto


@dataclass
class Topic:
    title: str
    id: str
    content: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    content_html: list[str] = field(default_factory=list)


class IndexDirection(Enum):
    NO_INDEX = auto()
    INDEX = auto()
    AUTO = auto()


@dataclass
class DiaryEntry:
    date: str
    index_direction: IndexDirection
    topics: list[Topic]
