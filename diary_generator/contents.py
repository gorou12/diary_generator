import json
import os
import re

from . import notion_api, utils
from .models import Config, DiaryEntry, Topic


def get(config: Config) -> list[DiaryEntry]:
    cache_file_name = config.cache_file_name
    use_cache = config.use_cache

    if use_cache and os.path.exists(cache_file_name):
        print("✅ キャッシュからデータを読み込みます")
        raw_data = _read_content_json(cache_file_name)
    else:
        raw_data = _read_notion_data(cache_file_name)

    return _parse_json_to_diary_entries(raw_data)


def _read_content_json(json_path: str) -> list[DiaryEntry]:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_content_json(json_path: str, content: any):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)


def _parse_json_to_diary_entries(raw_data: list) -> list[DiaryEntry]:
    entries = []
    for entry_data in raw_data:
        topics = [
            Topic(
                title=topic_data["title"],
                content=topic_data["content"],
                hashtags=topic_data["hashtags"],
            )
            for topic_data in entry_data["topics"]
        ]
        entry = DiaryEntry(date=entry_data["date"], topics=topics)
        entries.append(entry)
    return entries


def _read_notion_data(cache_file_name: str):
    print("🔄 Notion API からデータを取得中...")
    data = notion_api.query_database(utils.get_notion_database_id())

    all_pages = []
    for item in data.get("results", []):
        properties = item.get("properties", {})
        date = properties.get("日付", {}).get("date", {}).get("start", "")
        page_id = item.get("id", "")
        is_public = properties.get("公開", {}).get("checkbox", False)

        if not date or not is_public:
            continue  # 非公開ページはスキップ

        topics = _read_page_content(page_id)
        print(f"- 日付データ({date}) 取得完了")
        all_pages.append({"date": date, "topics": topics})

    _write_content_json(cache_file_name, all_pages)
    print("✅ Notionデータ取得＆キャッシュ完了")
    return all_pages


def _read_page_content(page_id: str) -> list:
    data = notion_api.get_block_children(page_id)

    blocks = data.get("results", [])
    topics = []
    current_topic = {"title": "", "content": [], "hashtags": []}

    for block in blocks:
        block_type = block.get("type")
        text_elements = (
            block[block_type].get("rich_text", []) if block_type in block else []
        )
        text_content = "".join(
            t["text"]["content"] for t in text_elements if "text" in t
        ).strip()

        if block_type == "heading_3":  # Notionの「見出し3」がトピック名に相当
            if current_topic["title"] and "非公開" not in current_topic["hashtags"]:
                topics.append(current_topic)  # 既存のトピックを保存

            current_topic = {"title": text_content, "content": [], "hashtags": []}
        elif text_content.startswith("#"):
            hashtags = re.findall(r"#(\S+)", text_content)
            current_topic["hashtags"].extend(hashtags)
        elif text_content:
            current_topic["content"].append(text_content.replace("\n", "<br>"))

    if current_topic["title"] and "非公開" not in current_topic["hashtags"]:
        topics.append(current_topic)

    return topics
