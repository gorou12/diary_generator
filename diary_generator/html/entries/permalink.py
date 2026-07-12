import os
import re
import shutil

from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry, Topic
from diary_generator.url_helpers import date_topic_url, entry_permalink
from diary_generator.util import utilities

log = logger.get_logger()


def _entries_root() -> str:
    return os.path.join(config.FILE_NAMES.OUTPUT_BASE_DIR_NAME, "entries")


def _description(topic: Topic) -> str:
    text = f"{topic.title} {' '.join(topic.content)} {' '.join('#' + tag for tag in topic.hashtags)}"
    text = re.sub(r"</?[a-zA-Z0-9][a-zA-Z0-9 '\"\-_.@&$%/]+>", "", text)
    text = re.sub(r"https?://[a-zA-Z0-9!?/+\-_~=;.,*&@#$%()'\[\]]+", "", text)
    return text[:120]


def iter_topic_targets(diary_entries: list[DiaryEntry]) -> list[tuple[DiaryEntry, Topic, int]]:
    per_page = config.PAGINATE.DATE_DETAIL_TOPICS
    targets: list[tuple[DiaryEntry, Topic, int]] = []
    for diary_entry in diary_entries:
        pages, _ = utilities.paginate_list(diary_entry.topics, per_page)
        if not pages:
            pages = [[]]
        for idx, page_topics in enumerate(pages):
            page_num = idx + 1
            for topic in page_topics:
                targets.append((diary_entry, topic, page_num))
    return targets


def generate(diary_entries: list[DiaryEntry]) -> None:
    root = _entries_root()
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root, exist_ok=True)

    for diary_entry, topic, page_num in iter_topic_targets(diary_entries):
        dest_url = date_topic_url(diary_entry.date, topic.id, page_num)
        out_path = os.path.join(root, topic.id, "index.html")
        context = {
            "dest_url": dest_url,
            "title": topic.title,
            "date": diary_entry.date,
            "description": _description(topic),
            "canonical_url": entry_permalink(topic.id),
        }
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        utilities.render_template("entry_redirect.html", context, out_path)

    log.info("✅ 小トピック恒久リンクページを生成しました！")
