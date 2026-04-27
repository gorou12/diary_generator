import json
import os
import re
import typing
from datetime import datetime, timedelta, timezone
from typing import Any

from diary_generator import notion_api
from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry, IndexDirection, Topic
from diary_generator.util import diarydiff
from diary_generator.util.img import generate_image_tag
from diary_generator.util.linkcard import cache, linkcard

log = logger.get_logger()

CACHE_SCHEMA_VERSION = 1
JST = timezone(timedelta(hours=9))


def get() -> list[DiaryEntry]:
    index_path = config.FILE_NAMES.CACHE_DIARY_INDEX_PATH
    detail_path = config.FILE_NAMES.CACHE_DIARY_DETAIL_PATH
    use_cache = config.USE_CACHE
    has_cache = os.path.exists(index_path) and os.path.exists(detail_path)

    if use_cache and has_cache and _is_valid_cache_pair(index_path, detail_path):
        log.info("✅ キャッシュからデータを読み込みます")
        index_cache = _read_json(index_path)
        detail_cache = _read_json(detail_path)
    else:
        old_index_cache: dict[str, Any] | None = None
        old_detail_cache: dict[str, Any] | None = None

        if has_cache and _is_valid_cache_pair(index_path, detail_path):
            old_index_cache = _read_json(index_path)
            old_detail_cache = _read_json(detail_path)

        index_entries = _fetch_diary_index_entries()
        detail_entries = _build_detail_entries(
            index_entries=index_entries,
            old_index_cache=old_index_cache,
            old_detail_cache=old_detail_cache,
        )

        generated_at = _now_iso()
        index_cache = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "generated_at": generated_at,
            "entries": index_entries,
        }
        detail_cache = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "generated_at": generated_at,
            "entries": detail_entries,
        }

        _write_json(index_path, index_cache)
        _write_json(detail_path, detail_cache)

        old_entries = old_detail_cache.get("entries", []) if old_detail_cache else []
        diarydiff.diff_detail_entries(old_entries, detail_entries)

    raw_data = _compose_raw_data_from_caches(index_cache, detail_cache)
    return _parse_json_to_diary_entries(raw_data)


def _is_valid_cache_pair(index_path: str, detail_path: str) -> bool:
    try:
        index_cache = _read_json(index_path)
        detail_cache = _read_json(detail_path)
    except Exception as e:
        log.warning("⚠️ キャッシュ読み込み失敗のため再取得します: %s", e)
        return False

    if index_cache.get("schema_version") != CACHE_SCHEMA_VERSION:
        return False
    if detail_cache.get("schema_version") != CACHE_SCHEMA_VERSION:
        return False
    return True


def _read_json(json_path: str) -> Any:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(json_path: str, content: Any):
    tmp_path = f"{json_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, json_path)
    log.info("✅ キャッシュ更新: %s", json_path)


def _parse_json_to_diary_entries(raw_data: list[dict[str, Any]]) -> list[DiaryEntry]:
    entries = []
    now = datetime.now(JST)
    cache.initialize()

    for entry_data in raw_data:
        topics = [
            Topic(
                title=topic_data["title"],
                id=topic_data["id"],
                content=topic_data["content"],
                content_html=linkcard.create(topic_data["content"]),
                hashtags=topic_data["hashtags"],
            )
            for topic_data in entry_data["topics"]
            if (  # ブロックを最後にいじってから5分後に収集対象とする
                now
                > _parse_iso_datetime(topic_data["last_edited_time"])
                + timedelta(minutes=5)
            )
        ]
        index_direction = _match_index_direction(entry_data["index_direction"])
        date = entry_data["date"]
        entry = DiaryEntry(
            date=date,
            date_jpn=f"{date[:4]}年{date[5:7]}月{date[8:10]}日",
            index_direction=index_direction,
            topics=topics,
        )
        entries.append(entry)

    # OGP用キャッシュ再書き込み
    cache.save_cache()
    return entries


def _fetch_diary_index_entries() -> list[dict[str, Any]]:
    log.info("🔄 Notion API から日記一覧を取得中...")
    entries = []
    cursor = None

    while True:
        data = notion_api.query_database(
            config.ENV.NOTION_DATABASE_ID, start_cursor=cursor
        )
        results = data.get("results", [])
        for item in results:
            properties = item.get("properties", {})
            date = properties.get("日付", {}).get("date", {}).get("start", "")
            page_id = item.get("id", "")
            is_public = properties.get("公開", {}).get("checkbox", False)
            can_index = properties.get("収集対象", {}).get("select", {})

            if not date or not is_public or not can_index:
                continue  # 非公開ページはスキップ

            page_last_edited = item.get("last_edited_time", "")
            entries.append(
                {
                    "page_id": page_id,
                    "page_name": _extract_page_name(properties, date),
                    "entry_date": date,
                    "index_direction": can_index.get("name", "noindex"),
                    "last_edited_time": page_last_edited,
                    "source_last_edited_time": page_last_edited,
                }
            )
        if not data.get("has_more"):
            break

        cursor = data.get("next_cursor")

    entries.sort(
        key=lambda entry: (
            entry.get("entry_date", ""),
            entry.get("page_id", ""),
        ),
        reverse=True,
    )
    log.info("✅ Notion一覧取得完了: %d 件", len(entries))
    return entries


def _extract_page_name(properties: dict[str, Any], entry_date: str) -> str:
    for prop_value in properties.values():
        if prop_value.get("type") != "title":
            continue
        title_items = prop_value.get("title", [])
        text = "".join(item.get("plain_text", "") for item in title_items).strip()
        if text:
            return text
    return entry_date.replace("-", "")


def _build_detail_entries(
    index_entries: list[dict[str, Any]],
    old_index_cache: dict[str, Any] | None,
    old_detail_cache: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    old_index_by_page_id: dict[str, dict[str, Any]] = {}
    old_detail_by_page_id: dict[str, dict[str, Any]] = {}

    if old_index_cache:
        old_index_by_page_id = {
            entry.get("page_id"): entry
            for entry in old_index_cache.get("entries", [])
            if entry.get("page_id")
        }
    if old_detail_cache:
        old_detail_by_page_id = {
            entry.get("page_id"): entry
            for entry in old_detail_cache.get("entries", [])
            if entry.get("page_id")
        }

    detail_entries = []
    for index_entry in index_entries:
        page_id = index_entry["page_id"]
        old_index_entry = old_index_by_page_id.get(page_id)
        old_detail_entry = old_detail_by_page_id.get(page_id)

        unchanged = (
            old_index_entry is not None
            and old_detail_entry is not None
            and old_index_entry.get("last_edited_time")
            == index_entry.get("last_edited_time")
        )
        if unchanged:
            detail_entries.append(
                {
                    **old_detail_entry,
                    "page_name": index_entry["page_name"],
                    "entry_date": index_entry["entry_date"],
                    "last_edited_time": index_entry["last_edited_time"],
                }
            )
            continue

        topics = _fetch_diary_page(page_id)
        detail_entries.append(
            {
                "page_id": page_id,
                "page_name": index_entry["page_name"],
                "entry_date": index_entry["entry_date"],
                "last_edited_time": index_entry["last_edited_time"],
                "topics": topics,
            }
        )
        log.debug("- 日付データ(%s) の詳細取得完了", index_entry["entry_date"])

    return detail_entries


def _fetch_diary_page(page_id: str) -> list[dict[str, Any]]:
    all_blocks = []
    cursor = None

    # ページネーションでブロックを取得
    while True:
        data = notion_api.get_block_children(page_id, start_cursor=cursor)
        results = data.get("results", [])
        all_blocks.extend(results)

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    topics: list[dict[str, Any]] = []
    current_topic = _new_topic()

    for block in all_blocks:
        block_type = block.get("type")
        text_content = _extract_text_content(block, block_type).strip()
        last_edited_time = block.get("last_edited_time") or _now_iso()

        if block_type == "heading_3":  # Notionの「見出し3」がトピック名に相当
            if not text_content:
                continue  # 空の見出しは無視
            _finalize_topic(topics, current_topic)
            current_topic = _new_topic(
                title=text_content,
                topic_id=block.get("id", ""),
                last_edited_time=last_edited_time,
            )
            _extend_unique(current_topic["tags"], _extract_hashtags(text_content))
        else:
            if not current_topic["title"]:
                continue
            _update_topic_last_edited_time(current_topic, last_edited_time)

            if text_content.startswith("#"):
                _extend_unique(current_topic["tags"], _extract_hashtags(text_content))
                continue

            normalized_block = _normalize_block(block)
            if normalized_block:
                current_topic["blocks"].append(normalized_block)

    _finalize_topic(topics, current_topic)
    return topics


def _new_topic(
    title: str = "",
    topic_id: str = "",
    last_edited_time: str = "",
) -> dict[str, Any]:
    return {
        "topic_id": topic_id,
        "title": title,
        "last_edited_time": last_edited_time or _now_iso(),
        "tags": [],
        "blocks": [],
        "plain_text": "",
    }


def _finalize_topic(topics: list[dict[str, Any]], topic: dict[str, Any]) -> None:
    if not topic.get("title"):
        return
    if "非公開" in topic.get("tags", []):
        return
    topic["plain_text"] = " ".join(
        block.get("plain_text", "")
        for block in topic.get("blocks", [])
        if block.get("plain_text")
    ).strip()
    topics.append(topic)


def _normalize_block(block: dict[str, Any]) -> dict[str, Any] | None:
    block_type = block.get("type")
    if not block_type:
        return None

    block_id = block.get("id", "")
    if block_type == "image":
        image = block.get("image", {})
        image_type = image.get("type")
        image_url = ""
        if image_type == "external":
            image_url = image.get("external", {}).get("url", "")
        elif image_type == "file":
            image_url = image.get("file", {}).get("url", "")
        if not image_url:
            return {"block_id": block_id, "type": block_type}
        return {
            "block_id": block_id,
            "type": block_type,
            "image": {"url": image_url, "source_type": image_type},
        }

    block_data = block.get(block_type, {})
    if not isinstance(block_data, dict):
        return {"block_id": block_id, "type": block_type}

    rich_text = block_data.get("rich_text", [])
    normalized_rich_text = []
    plain_parts = []
    for item in rich_text:
        normalized_item = _normalize_rich_text(item)
        if normalized_item:
            normalized_rich_text.append(normalized_item)
            plain_parts.append(normalized_item.get("text", ""))

    normalized = {
        "block_id": block_id,
        "type": block_type,
    }
    plain_text = "".join(plain_parts).strip()
    if plain_text:
        normalized["plain_text"] = plain_text
    if normalized_rich_text:
        normalized["rich_text"] = normalized_rich_text
    return normalized


def _normalize_rich_text(item: dict[str, Any]) -> dict[str, Any]:
    item_type = item.get("type")
    type_data = item.get(item_type, {}) if item_type else {}
    text = ""
    if isinstance(type_data, dict):
        text = type_data.get("content", "") or item.get("plain_text", "")
    else:
        text = item.get("plain_text", "")
    if not text and not item.get("href"):
        return {}
    return {
        "type": item_type,
        "text": text,
        "href": item.get("href"),
        "annotations": item.get("annotations", {}),
    }


def _extract_text_content(block: dict[str, Any], block_type: str | None) -> str:
    if not block_type:
        return ""
    block_data = block.get(block_type, {})
    if not isinstance(block_data, dict):
        return ""
    rich_text = block_data.get("rich_text", [])
    return "".join(item.get("plain_text", "") for item in rich_text)


def _extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#(\S+)", text)


def _extend_unique(tags: list[str], values: list[str]) -> None:
    for value in values:
        if value not in tags:
            tags.append(value)


def _update_topic_last_edited_time(topic: dict[str, Any], candidate: str) -> None:
    current = topic.get("last_edited_time")
    if not current:
        topic["last_edited_time"] = candidate
        return
    if _parse_iso_datetime(candidate) > _parse_iso_datetime(current):
        topic["last_edited_time"] = candidate


def _compose_raw_data_from_caches(
    index_cache: dict[str, Any],
    detail_cache: dict[str, Any],
) -> list[dict[str, Any]]:
    detail_by_page_id = {
        entry.get("page_id"): entry
        for entry in detail_cache.get("entries", [])
        if entry.get("page_id")
    }

    raw_data = []
    for index_entry in index_cache.get("entries", []):
        page_id = index_entry.get("page_id")
        detail_entry = detail_by_page_id.get(page_id)
        if not detail_entry:
            continue

        topics = []
        for topic in detail_entry.get("topics", []):
            topics.append(
                {
                    "title": topic.get("title", ""),
                    "id": topic.get("topic_id", ""),
                    "content": _build_topic_content(topic),
                    "hashtags": topic.get("tags", []),
                    "last_edited_time": topic.get("last_edited_time")
                    or detail_entry.get("last_edited_time")
                    or _now_iso(),
                }
            )

        raw_data.append(
            {
                "date": index_entry.get("entry_date", ""),
                "index_direction": index_entry.get("index_direction", "noindex"),
                "topics": topics,
            }
        )

    raw_data.sort(key=lambda item: item.get("date", ""), reverse=True)
    return raw_data


def _build_topic_content(topic: dict[str, Any]) -> list[str]:
    content = []
    for block in topic.get("blocks", []):
        block_type = block.get("type")
        if block_type == "image":
            image = block.get("image", {})
            image_url = image.get("url")
            block_id = block.get("block_id")
            if image_url and block_id:
                content.append(generate_image_tag(block_id, image_url))
            continue

        plain_text = block.get("plain_text", "")
        if plain_text:
            content.append(plain_text.replace("\n", "<br>"))
    return content


def _parse_iso_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def _now_iso() -> str:
    return datetime.now(JST).isoformat()


def _match_index_direction(val: str) -> IndexDirection:
    match val:
        case "index":
            return IndexDirection.INDEX
        case "noindex":
            return IndexDirection.NO_INDEX
        case "auto":
            return IndexDirection.AUTO
        case _ as unreachable:
            typing.assert_never(unreachable)
