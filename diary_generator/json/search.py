import json

from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry
from diary_generator.url_helpers import entry_permalink

log = logger.get_logger()


def generate(diary_entries: list[DiaryEntry]):
    """全文検索用の search_data.json を生成する"""
    log.info("🔄 本文検索用データ (search_data.json) を生成中...")

    output_path = config.FILE_NAMES.OUTPUT_JSON_DIR_NAME
    search_items = []

    for diary_entry in diary_entries:
        date = diary_entry.date
        for topic in diary_entry.topics:
            title = topic.title
            content_text = " ".join(topic.content)  # 段落を結合して1つの文字列に
            hashtags = " ".join(
                f"#{tag}" for tag in topic.hashtags
            )  # ハッシュタグも含める
            full_content = f"{content_text} {hashtags}"  # 本文 + タグ

            search_items.append(
                {
                    "date": date,
                    "title": title,
                    "content": full_content,
                    "topic_id": topic.id,
                    "url": entry_permalink(topic.id),
                }
            )

    # JSONファイルとして保存
    with open(f"{output_path}search_data.json", "w", encoding="utf-8") as f:
        json.dump(search_items, f, ensure_ascii=False, indent=2)

    log.info(f"✅ search_data.json を {len(search_items)} 件生成しました！")
