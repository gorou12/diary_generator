import json
import os
import re
import typing
from datetime import datetime, timedelta, timezone

from diary_generator import notion_api
from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry, IndexDirection, Topic
from diary_generator.util import diarydiff
from diary_generator.util.img import generate_image_tag
from diary_generator.util.linkcard import cache, linkcard

log = logger.get_logger()


def get() -> list[DiaryEntry]:
    cache_file_name = config.FILE_NAMES.CACHE_DIARY_PATH
    use_cache = config.USE_CACHE

    if use_cache and os.path.exists(cache_file_name):
        log.info("✅ キャッシュからデータを読み込みます")
        raw_data = _read_json(cache_file_name)
    else:
        diarydiff.copy_previous_json()
        raw_data = _fetch_diary_db()
        _write_json(cache_file_name, raw_data)
        diarydiff.diff_diary_json()

    return _parse_json_to_diary_entries(raw_data)


def _read_json(json_path: str) -> list[DiaryEntry]:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
    log.info("✅ ロード完了")


def _write_json(json_path: str, content: any):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    log.info("✅ キャッシュ完了")


def _parse_json_to_diary_entries(raw_data: list) -> list[DiaryEntry]:
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
            if (  # ブロックを最後にいじってから5分後に収集対象とする
                datetime.now(timezone(timedelta(hours=9)))
                > datetime.fromisoformat(topic_data["last_edited_time"])
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


def _fetch_diary_db():
    log.info("🔄 Notion API からデータを取得中...")

    all_pages = []
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

            index_direction = can_index.get("name", "noindex")

            topics = _fetch_diary_page(page_id)
            log.debug(f"- 日付データ({date}) 取得完了")
            all_pages.append(
                {"date": date, "index_direction": index_direction, "topics": topics}
            )
        if not data.get("has_more"):
            break

        cursor = data.get("next_cursor")

    log.info("✅ Notionデータ取得")
    return all_pages


def _fetch_diary_page(page_id: str) -> list:
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

    topics = []
    current_topic = {
        "title": "",
        "last_edited_time": "",
        "id": "",
        "content": [],
        "hashtags": [],
    }

    for block in all_blocks:
        block_type = block.get("type")
        block_id = block.get("id")
        text_elements = (
            block[block_type].get("rich_text", []) if block_type in block else []
        )
        text_content = "".join(
            t["text"]["content"] for t in text_elements if "text" in t
        ).strip()
        last_edited_time = block.get("last_edited_time")

        if block_type == "heading_3":  # Notionの「見出し3」がトピック名に相当
            if not text_content:
                continue  # 空の見出しは無視
            if current_topic["title"] and "非公開" not in current_topic["hashtags"]:
                topics.append(current_topic)  # 既存のトピックを保存
            current_topic = {
                "title": text_content,
                "id": block_id,
                "last_edited_time": "",
                "content": [],
                "hashtags": [],
            }
        elif block_type == "image":  # 画像
            if block["type"] == "image":
                if block["image"]["type"] == "external":
                    url = block["image"]["external"]["url"]
                elif block["image"]["type"] == "file":
                    url = block["image"]["file"]["url"]
                else:
                    continue
                id = block.get("id")
                current_topic["content"].append(generate_image_tag(id, url))
        elif text_content.startswith("#"):
            hashtags = re.findall(r"#(\S+)", text_content)
            current_topic["hashtags"].extend(hashtags)
        elif text_content:
            current_topic["content"].append(text_content.replace("\n", "<br>"))

        # トピック単位で最終更新日時を保存
        if not (current_topic.get("last_edited_time")):
            current_topic["last_edited_time"] = last_edited_time
        elif datetime.fromisoformat(last_edited_time) > datetime.fromisoformat(
            current_topic.get("last_edited_time")
        ):
            current_topic["last_edited_time"] = last_edited_time

    if current_topic["title"] and "非公開" not in current_topic["hashtags"]:
        topics.append(current_topic)

    return topics


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
