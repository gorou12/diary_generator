"""
公開 API: トピック URL 解決。

- データ供給・キャッシュ: `topic_slugs.load`（Notion / cache/topic_slugs.json）
- 正規化・解決: `topic_slugs.resolve` / `topic_slugs.normalize`
"""

from diary_generator.models import TopicSlugEntry
from diary_generator.topic_slugs.load import load_topic_slug_lookups
from diary_generator.topic_slugs.normalize import normalize_topic_key
from diary_generator.topic_slugs.resolve import TopicSlugResolver as _TopicSlugResolver


class TopicSlugResolver(_TopicSlugResolver):
    """
    トピック名（見出し / ハッシュタグ）から canonical URL を決定する。
    手動スラッグは Notion（または cache/topic_slugs.json）由来。無ければ自動スラッグ t-xxxxxxxxxx。
    """

    def __init__(self):
        manual, slug_to_display = load_topic_slug_lookups()
        super().__init__(manual, slug_to_display)


__all__ = [
    "TopicSlugResolver",
    "TopicSlugEntry",
    "normalize_topic_key",
]
