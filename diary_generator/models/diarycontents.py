from dataclasses import dataclass, field


@dataclass
class Topic:
    title: str
    content: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)


@dataclass
class DiaryEntry:
    date: str
    topics: list[Topic]
