from dataclasses import dataclass, field

from .. import util


@dataclass
class Topic:
    title: str
    content: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    content_html: list[str] = field(init=False)

    def __post_init__(self):
        self.content_html = util.convert_contents_link_card(self.content)


@dataclass
class DiaryEntry:
    date: str
    topics: list[Topic]
