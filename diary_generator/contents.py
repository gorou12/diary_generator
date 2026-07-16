import html
import json
import os
import re
import typing
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from diary_generator import notion_api
from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry, IndexDirection, Topic
from diary_generator.util import diarydiff
from diary_generator.util.img import generate_image_tag
from diary_generator.util.linkcard import cache, linkcard

log = logger.get_logger()

CACHE_SCHEMA_VERSION = 3
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

        now = datetime.now(JST)
        index_entries = _fetch_diary_index_entries()
        detail_entries = _build_detail_entries(
            index_entries=index_entries,
            old_index_cache=old_index_cache,
            old_detail_cache=old_detail_cache,
            now=now,
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
    now: datetime,
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

        # has_pending_topics=True なら前回保留あり → last_edited_time が変わっていなくても強制再取得
        unchanged = (
            old_index_entry is not None
            and old_detail_entry is not None
            and old_index_entry.get("last_edited_time")
            == index_entry.get("last_edited_time")
            and not old_detail_entry.get("has_pending_topics", False)
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

        topics, has_pending = _fetch_diary_page(page_id, now)
        detail_entries.append(
            {
                "page_id": page_id,
                "page_name": index_entry["page_name"],
                "entry_date": index_entry["entry_date"],
                "last_edited_time": index_entry["last_edited_time"],
                "topics": topics,
                "has_pending_topics": has_pending,
            }
        )
        log.debug("- 日付データ(%s) の詳細取得完了", index_entry["entry_date"])

    return detail_entries


def _fetch_diary_page(page_id: str, now: datetime) -> tuple[list[dict[str, Any]], bool]:
    """ページのブロックを取得してトピックに変換する。
    戻り値: (topics, has_pending_topics)
    has_pending_topics が True の場合、5分未満フィルタで除外されたトピックが存在する。
    """
    all_blocks = _fetch_block_children_recursive(page_id)

    topics: list[dict[str, Any]] = []
    current_topic = _new_topic()
    has_pending = False

    for block in all_blocks:
        block_type = block.get("type")
        text_content = _extract_text_content(block, block_type).strip()
        last_edited_time = block.get("last_edited_time") or _now_iso()

        if block_type == "heading_3":  # Notionの「見出し3」がトピック名に相当
            if not text_content:
                continue  # 空の見出しは無視
            pending = _finalize_topic(topics, current_topic, now)
            has_pending = has_pending or pending
            current_topic = _new_topic(
                title=text_content,
                topic_id=block.get("id", ""),
                last_edited_time=last_edited_time,
            )
            _extend_unique(current_topic["tags"], _extract_hashtags(text_content))
        else:
            if not current_topic["title"]:
                continue
            if block_type == "paragraph" and text_content.startswith("#"):
                _extend_unique(current_topic["tags"], _extract_hashtags(text_content))
                continue

            normalized_block = _normalize_block(block)
            if normalized_block:
                current_topic["blocks"].append(normalized_block)

    pending = _finalize_topic(topics, current_topic, now)
    has_pending = has_pending or pending
    return topics, has_pending


def _fetch_block_children_recursive(block_id: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    cursor = None

    while True:
        data = notion_api.get_block_children(block_id, start_cursor=cursor)
        results = data.get("results", [])
        for block in results:
            if block.get("has_children"):
                block["children"] = _fetch_block_children_recursive(block.get("id", ""))
            blocks.append(block)

        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")

    return blocks


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


def _finalize_topic(
    topics: list[dict[str, Any]],
    topic: dict[str, Any],
    now: datetime,
) -> bool:
    """トピックを確定してリストに追加する。戻り値は has_pending（5分未満で保留した場合 True）。"""
    if not topic.get("title"):
        return False
    if "非公開" in topic.get("tags", []):
        return False  # 確定除外（保留ではない）
    effective_blocks = _trim_trailing_empty_paragraphs(topic.get("blocks", []))
    topic["last_edited_time"] = (
        _latest_block_last_edited_time(effective_blocks)
        or topic.get("last_edited_time")
        or _now_iso()
    )
    if (
        _parse_iso_datetime(topic["last_edited_time"])
        + timedelta(seconds=config.TOPIC_PENDING_TIME)
        > now
    ):
        return True  # PendingTime未満: キャッシュに含めず保留
    topic["blocks"] = [_strip_block_runtime_fields(block) for block in effective_blocks]
    topic["plain_text"] = " ".join(
        _iter_block_plain_text(topic.get("blocks", []))
    ).strip()
    topics.append(topic)
    return False


def _iter_block_plain_text(blocks: list[dict[str, Any]]):
    for block in blocks:
        if block.get("plain_text"):
            yield block["plain_text"]
        children = block.get("children")
        if isinstance(children, list):
            yield from _iter_block_plain_text(children)


def _trim_trailing_empty_paragraphs(
    blocks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    end = len(blocks)
    while end > 0 and _is_empty_paragraph_block(blocks[end - 1]):
        end -= 1
    return blocks[:end]


def _is_empty_paragraph_block(block: dict[str, Any]) -> bool:
    return block.get("type") == "paragraph" and not block.get("plain_text", "").strip()


def _latest_block_last_edited_time(blocks: list[dict[str, Any]]) -> str:
    latest = ""
    for block in blocks:
        candidates = [block.get("_last_edited_time", "")]
        children = block.get("children")
        if isinstance(children, list):
            candidates.append(_latest_block_last_edited_time(children))
        for candidate in candidates:
            if not candidate:
                continue
            if not latest or _parse_iso_datetime(candidate) > _parse_iso_datetime(
                latest
            ):
                latest = candidate
    return latest


def _strip_block_runtime_fields(block: dict[str, Any]) -> dict[str, Any]:
    stripped = {key: value for key, value in block.items() if not key.startswith("_")}
    children = stripped.get("children")
    if isinstance(children, list):
        stripped["children"] = [
            _strip_block_runtime_fields(child) for child in children
        ]
    return stripped


def _normalize_block(block: dict[str, Any]) -> dict[str, Any] | None:
    block_type = block.get("type")
    if not block_type:
        return None

    block_id = block.get("id", "")
    last_edited_time = block.get("last_edited_time") or _now_iso()

    if block_type == "image":
        image = block.get("image", {})
        image_type = image.get("type")
        image_url = ""
        if image_type == "external":
            image_url = image.get("external", {}).get("url", "")
        elif image_type == "file":
            image_url = image.get("file", {}).get("url", "")

        normalized = {"block_id": block_id, "type": block_type}
        if image_url:
            normalized["image"] = {"url": image_url, "source_type": image_type}
        _attach_normalized_children(normalized, block)
        normalized["_last_edited_time"] = last_edited_time
        return normalized

    block_data = block.get(block_type, {})
    if not isinstance(block_data, dict):
        return {"block_id": block_id, "type": block_type}

    normalized_rich_text = _normalize_rich_text_items(block_data.get("rich_text", []))

    normalized = {
        "block_id": block_id,
        "type": block_type,
    }
    plain_text = "".join(item.get("text", "") for item in normalized_rich_text).strip()
    if plain_text:
        normalized["plain_text"] = plain_text
    if normalized_rich_text:
        normalized["rich_text"] = normalized_rich_text

    if block_type == "to_do":
        normalized["checked"] = bool(block_data.get("checked", False))
    elif block_type == "callout":
        icon = block_data.get("icon")
        if isinstance(icon, dict):
            normalized["icon"] = _normalize_icon(icon)

    _attach_normalized_children(normalized, block)
    normalized["_last_edited_time"] = last_edited_time
    return normalized


def _attach_normalized_children(
    normalized: dict[str, Any], block: dict[str, Any]
) -> None:
    children = block.get("children")
    if not isinstance(children, list):
        return
    normalized_children = []
    for child in children:
        normalized_child = _normalize_block(child)
        if normalized_child:
            normalized_children.append(normalized_child)
    if normalized_children:
        normalized["children"] = normalized_children


def _normalize_rich_text_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_items = []
    for item in items:
        normalized_item = _normalize_rich_text(item)
        if normalized_item:
            normalized_items.append(normalized_item)
    return normalized_items


def _normalize_icon(icon: dict[str, Any]) -> dict[str, Any]:
    icon_type = icon.get("type")
    normalized = {"type": icon_type}
    if icon_type == "emoji":
        normalized["emoji"] = icon.get("emoji", "")
    elif icon_type in {"external", "file"}:
        normalized["url"] = icon.get(icon_type, {}).get("url", "")
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
    return render_blocks(topic.get("blocks", []))


def render_blocks(blocks: list[dict[str, Any]]) -> list[str]:
    content: list[str] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        block_type = block.get("type")
        if block_type in {"bulleted_list_item", "numbered_list_item"}:
            list_type = block_type
            items = []
            while index < len(blocks) and blocks[index].get("type") == list_type:
                item_html = _render_list_item(blocks[index])
                if item_html:
                    items.append(item_html)
                index += 1
            if items:
                tag = "ul" if list_type == "bulleted_list_item" else "ol"
                content.append(f"<{tag}>" + "".join(items) + f"</{tag}>")
            continue

        rendered = render_block(block)
        if rendered:
            content.append(rendered)
        index += 1
    return content


def _render_list_item(block: dict[str, Any]) -> str | None:
    inner = _render_text_block_inner(block)
    child_html = _render_list_item_children(block)
    if not inner and not child_html:
        return None
    return f"<li>{inner}{child_html}</li>"


def _render_list_item_children(block: dict[str, Any]) -> str:
    children = block.get("children")
    if not isinstance(children, list) or not children:
        return ""

    list_children = []
    for child in children:
        if _is_list_item_block(child):
            list_children.append(child)
        else:
            _warn_skipped_list_item_child(block, child)
    return "".join(render_blocks(list_children))


def _is_list_item_block(block: dict[str, Any]) -> bool:
    return block.get("type") in {"bulleted_list_item", "numbered_list_item"}


def _warn_skipped_list_item_child(
    parent: dict[str, Any], child: dict[str, Any]
) -> None:
    log.warning(
        "⚠️ Notion list item has unsupported child block; child HTML output was skipped: "
        "parent_block_id=%s parent_type=%s child_block_id=%s child_type=%s",
        parent.get("block_id") or parent.get("id", ""),
        parent.get("type", ""),
        child.get("block_id") or child.get("id", ""),
        child.get("type", ""),
    )


def _warn_if_unsupported_child_blocks(block: dict[str, Any]) -> None:
    children = block.get("children")
    if not isinstance(children, list) or not children or _is_list_item_block(block):
        return

    log.warning(
        "⚠️ Notion block has unsupported child blocks; child HTML output was skipped: "
        "block_id=%s type=%s child_count=%d",
        block.get("block_id") or block.get("id", ""),
        block.get("type", ""),
        len(children),
    )


def render_block(block: dict[str, Any]) -> str | None:
    _warn_if_unsupported_child_blocks(block)
    block_type = block.get("type")
    match block_type:
        case "paragraph":
            inner = _render_text_block_inner(block)
            if inner:
                return f"<p>{inner}</p>"
            return "<br>"
        case "image":
            return _render_image_block(block)
        case "bulleted_list_item" | "numbered_list_item":
            inner = _render_text_block_inner(block)
            return f"<li>{inner}</li>" if inner else None
        case "to_do":
            inner = _render_text_block_inner(block)
            if not inner:
                return None
            checked = " checked" if block.get("checked") else ""
            return (
                '<label class="todo">'
                f'<input type="checkbox" disabled{checked}>'
                f"<span>{inner}</span></label>"
            )
        case "quote":
            inner = _render_text_block_inner(block)
            return f"<blockquote>{inner}</blockquote>" if inner else None
        case "callout":
            inner = _render_text_block_inner(block)
            icon = _render_callout_icon(block.get("icon"))
            if not inner and not icon:
                return None
            return f'<div class="callout">{icon}<div>{inner}</div></div>'
        case "divider":
            return "<hr>"
        case "heading_4":
            inner = _render_text_block_inner(block)
            return f"<h4>{inner}</h4>" if inner else None
        case "heading_3":
            return None
        case _:
            inner = _render_text_block_inner(block)
            return f"<p>{inner}</p>" if inner else None


def _render_text_block_inner(block: dict[str, Any]) -> str:
    rich_text = block.get("rich_text")
    if isinstance(rich_text, list) and rich_text:
        if _is_standalone_url_paragraph(block):
            return html.escape(str(rich_text[0].get("text", ""))).replace("\n", "<br>")
        return "".join(_render_rich_text_item(item) for item in rich_text).replace(
            "\n", "<br>"
        )
    return html.escape(str(block.get("plain_text", ""))).replace("\n", "<br>")


def _is_standalone_url_paragraph(block: dict[str, Any]) -> bool:
    if block.get("type") != "paragraph":
        return False
    rich_text = block.get("rich_text")
    if not isinstance(rich_text, list) or len(rich_text) != 1:
        return False
    item = rich_text[0]
    text = str(item.get("text", ""))
    href = item.get("href")
    if not href or text != str(href):
        return False
    return urlparse(text).scheme.lower() in {"https", "http"}


def _render_rich_text_item(item: dict[str, Any]) -> str:
    text = html.escape(str(item.get("text", ""))).replace("\n", "<br>")
    annotations = (
        item.get("annotations") if isinstance(item.get("annotations"), dict) else {}
    )
    if annotations.get("code"):
        text = f"<code>{text}</code>"
    if annotations.get("bold"):
        text = f"<strong>{text}</strong>"
    if annotations.get("italic"):
        text = f"<em>{text}</em>"
    if annotations.get("strikethrough"):
        text = f"<s>{text}</s>"
    if annotations.get("underline"):
        text = f"<u>{text}</u>"
    href = item.get("href")
    if href and _is_allowed_url_scheme(str(href)):
        escaped_href = html.escape(str(href), quote=True)
        text = f'<a href="{escaped_href}" target="_blank" rel="noopener noreferrer">{text}</a>'
    return text


def _is_allowed_url_scheme(url: str) -> bool:
    return urlparse(url).scheme.lower() in {"https", "http", "mailto"}


def _render_image_block(block: dict[str, Any]) -> str | None:
    image = block.get("image", {})
    image_url = image.get("url") if isinstance(image, dict) else None
    block_id = block.get("block_id")
    if not image_url or not block_id:
        return None
    return generate_image_tag(block_id, image_url)


def _render_callout_icon(icon: Any) -> str:
    if not isinstance(icon, dict):
        return ""
    if icon.get("type") == "emoji" and icon.get("emoji"):
        return f'<span class="callout-icon">{html.escape(str(icon["emoji"]))}</span>'
    if icon.get("url") and _is_allowed_url_scheme(str(icon["url"])):
        return (
            '<img class="callout-icon" alt="" '
            f'src="{html.escape(str(icon["url"]), quote=True)}">'
        )
    return ""


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
