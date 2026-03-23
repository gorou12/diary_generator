"""Notion または cache/topic_slugs.json からルールを読み、TopicSlugResolver を組み立てる。"""

from __future__ import annotations

import json
import os

from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import TopicSlugEntry
from diary_generator.topic_slugs.entries import page_to_entry
from diary_generator.topic_slugs.notion_fetch import fetch_all_slug_database_pages
from diary_generator.topic_slugs.resolve import (
    TopicSlugResolver,
    build_lookup,
    build_slug_to_display_name,
)

log = logger.get_logger()


def _write_json(path: str, content: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)


def _read_json(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return raw if isinstance(raw, list) else []


def load_topic_slug_rules() -> list[dict]:
    """
    cache/topic_slugs.json 互換のリストを返す。
    USE_TOPIC_SLUG_CACHE かつファイルがあれば読む。無ければ Notion から取得してキャッシュに書く。
    """
    path = config.FILE_NAMES.CACHE_TOPIC_SLUGS_PATH
    use_cache = config.USE_TOPIC_SLUG_CACHE

    if use_cache and os.path.exists(path):
        log.info("✅ トピックスラッグをキャッシュから読み込みます")
        try:
            return _read_json(path)
        except Exception as e:
            log.warning("トピックスラッグキャッシュの読み込みに失敗しました: %s", e)
            return []

    database_id = (config.ENV.SLUG_DATABASE_ID or "").strip()
    if not database_id:
        log.warning("SLUG_DATABASE_ID が空のためトピックスラッグは読み込めません")
        return []

    try:
        pages = fetch_all_slug_database_pages(database_id)
    except Exception as e:
        log.warning("トピックスラッグの Notion 取得に失敗しました: %s", e)
        if os.path.exists(path):
            try:
                log.info("既存の cache/topic_slugs.json をフォールバックとして読みます")
                return _read_json(path)
            except Exception as e2:
                log.warning("フォールバック読み込みも失敗: %s", e2)
        return []

    entries: list[TopicSlugEntry] = []
    for p in pages:
        ent = page_to_entry(p)
        if ent:
            entries.append(ent)

    rules = [e.to_dict() for e in entries]
    try:
        _write_json(path, rules)
    except Exception as e:
        log.warning("topic_slugs.json の書き込みに失敗しました: %s", e)

    log.info("✅ トピックスラッグを Notion から取得しました（%d 件）", len(rules))
    return rules


def load_topic_slug_lookups() -> tuple[dict[str, str], dict[str, str]]:
    """正規化キー → slug と、slug → 表示用正式名。"""
    rules = load_topic_slug_rules()
    entries = [TopicSlugEntry.from_dict(r) for r in rules]
    return build_lookup(entries), build_slug_to_display_name(entries)


def load_manual_lookup() -> dict[str, str]:
    """TopicSlugResolver 用の正規化キー → slug 辞書。"""
    return load_topic_slug_lookups()[0]


def create_topic_slug_resolver() -> TopicSlugResolver:
    manual, slug_to_display = load_topic_slug_lookups()
    return TopicSlugResolver(manual, slug_to_display)
