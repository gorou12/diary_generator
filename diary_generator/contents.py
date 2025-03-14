import json
import os
import re

from diary_generator import notion_api
from diary_generator.config.configuration import config
from diary_generator.models import DiaryEntry, Topic
from diary_generator.util.img import generate_image_tag
from diary_generator.util.linkcard import cache, linkcard


def get() -> list[DiaryEntry]:
    cache_file_name = config.FILE_NAMES.CACHE_DIARY_PATH
    use_cache = config.USE_CACHE

    if use_cache and os.path.exists(cache_file_name):
        print("✅ キャッシュからデータを読み込みます")
        raw_data = _read_json(cache_file_name)
    else:
        raw_data = _fetch_diary_db()
        _write_json(cache_file_name, raw_data)

    return _parse_json_to_diary_entries(raw_data)


def _read_json(json_path: str) -> list[DiaryEntry]:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
    print("✅ ロード完了")


def _write_json(json_path: str, content: any):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    print("✅ キャッシュ完了")


def _parse_json_to_diary_entries(raw_data: list) -> list[DiaryEntry]:
    entries = []

    cache.initialize()

    for entry_data in raw_data:
        topics = [
            Topic(
                title=topic_data["title"],
                content=topic_data["content"],
                content_html=linkcard.create(topic_data["content"]),
                hashtags=topic_data["hashtags"],
            )
            for topic_data in entry_data["topics"]
        ]
        entry = DiaryEntry(date=entry_data["date"], topics=topics)
        entries.append(entry)

    # OGP用キャッシュ再書き込み
    cache.save_cache()
    return entries


def _fetch_diary_db():
    print("🔄 Notion API からデータを取得中...")
    data = notion_api.query_database(config.ENV.NOTION_DATABASE_ID)

    all_pages = []
    for item in data.get("results", []):
        properties = item.get("properties", {})
        date = properties.get("日付", {}).get("date", {}).get("start", "")
        page_id = item.get("id", "")
        is_public = properties.get("公開", {}).get("checkbox", False)

        if not date or not is_public:
            continue  # 非公開ページはスキップ

        topics = _fetch_diary_page(page_id)
        print(f"- 日付データ({date}) 取得完了")
        all_pages.append({"date": date, "topics": topics})

    print("✅ Notionデータ取得")
    return all_pages


def _fetch_diary_page(page_id: str) -> list:
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
        elif block_type == "image":  # 画像
            if block["type"] == "image":
                if block["image"]["type"] == "external":
                    url = block["image"]["external"]["url"]
                elif block["image"]["type"] == "file":
                    url = block["image"]["file"]["url"]
                else:
                    continue  # 不明なタイプなら無視
                id = block.get("id")
                current_topic["content"].append(generate_image_tag(id, url))
        elif text_content.startswith("#"):
            hashtags = re.findall(r"#(\S+)", text_content)
            current_topic["hashtags"].extend(hashtags)
        elif text_content:
            current_topic["content"].append(text_content.replace("\n", "<br>"))

    if current_topic["title"] and "非公開" not in current_topic["hashtags"]:
        topics.append(current_topic)

    return topics
