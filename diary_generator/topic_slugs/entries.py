"""Notion ページを内部表現 TopicSlugEntry に変換する。"""

from __future__ import annotations

from diary_generator.models import TopicSlugEntry

# Notion DB のプロパティ名（サンプルに合わせ固定）
PROP_NAME = "名前"
PROP_SLUG = "スラッグ"
PROP_ALIASES = "エイリアス"


def _plain_title(props: dict, key: str) -> str:
    block = props.get(key) or {}
    if block.get("type") != "title":
        return ""
    parts = block.get("title") or []
    return "".join(p.get("plain_text", "") for p in parts)


def _plain_rich_text(props: dict, key: str) -> str:
    block = props.get(key) or {}
    if block.get("type") != "rich_text":
        return ""
    parts = block.get("rich_text") or []
    return "".join(p.get("plain_text", "") for p in parts)


def page_to_entry(page: dict) -> TopicSlugEntry | None:
    """Notion のページ 1 件から TopicSlugEntry を作る。欠損・空スラッグは None。"""
    if page.get("in_trash") or page.get("archived"):
        return None
    props = page.get("properties") or {}
    name = _plain_title(props, PROP_NAME).strip()
    slug_raw = _plain_rich_text(props, PROP_SLUG).strip()
    aliases_raw = _plain_rich_text(props, PROP_ALIASES)

    slug = slug_raw.strip().strip("/")
    if not name or not slug:
        return None

    aliases: list[str] = []
    for line in aliases_raw.splitlines():
        s = line.strip()
        if s:
            aliases.append(s)

    return TopicSlugEntry(name=name, slug=slug, aliases=aliases)
