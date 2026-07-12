import os
import re

from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry, IndexDirection, Topic
from diary_generator.util import utilities

log = logger.get_logger()


def _date_url(date: str, page_num: int = 1) -> str:
    if page_num <= 1:
        return f"/dates/{date}.html"
    return f"/dates/{date}/page/{page_num}/"


def _date_output_path(dates_dir: str, date: str, page_num: int = 1) -> str:
    if page_num <= 1:
        return f"{dates_dir}{date}.html"
    return os.path.join(dates_dir, date, "page", str(page_num), "index.html")


def _build_pagination_html(date: str, page_num: int, total_pages: int) -> str:
    if total_pages <= 1:
        return ""

    pagination = ""
    if page_num > 1:
        pagination += f'<a href="{_date_url(date, page_num - 1)}">« 前へ</a> '
    pagination += f"<span>{page_num}/{total_pages}</span>"
    if page_num < total_pages:
        pagination += f' <a href="{_date_url(date, page_num + 1)}">次へ »</a>'
    return pagination


def generate(diary_entries: list[DiaryEntry]):
    dates_dir = config.FILE_NAMES.OUTPUT_DATES_DIR_NAME
    dates_nav = _create_dates_nav(diary_entries)
    per_page_topics = config.PAGINATE.DATE_DETAIL_TOPICS

    for diary_entry in diary_entries:
        date = diary_entry.date
        topics = diary_entry.topics
        description = _generate_description(diary_entry.topics)
        should_index = _judge_index(diary_entry.index_direction, topics)
        pages, total_pages = utilities.paginate_list(topics, per_page_topics)
        if not pages:
            pages = [[]]
            total_pages = 1

        for idx, page_topics in enumerate(pages):
            page_num = idx + 1
            context = {
                "title": f"日記 - {date}",
                "should_index": should_index,
                "description": description,
                "date": date,
                "initial_month": date[:7],
                "topics": page_topics,
                "pagination": _build_pagination_html(date, page_num, total_pages),
                "prev_date": dates_nav[date]["prev"],
                "next_date": dates_nav[date]["next"],
                "newest_date": dates_nav[date]["newest"],
                "canonical_url": _date_url(date, page_num),
            }
            output_file = _date_output_path(dates_dir, date, page_num)
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            utilities.render_template("date.html", context, output_file)
    log.info("✅ 日付ページを生成しました！")


def _create_dates_nav(diary_entries: list[DiaryEntry]) -> dict:
    sorted_dates = sorted([d.date for d in diary_entries])
    newest_date = sorted_dates[-1]
    dates_nav = {}
    for i, date in enumerate(sorted_dates):
        prev_date = sorted_dates[i - 1] if i > 0 else None
        next_date = sorted_dates[i + 1] if i < (len(sorted_dates) - 1) else None
        dates_nav[date] = {"prev": prev_date, "next": next_date, "newest": newest_date}

    return dates_nav


def _judge_index(direction: IndexDirection, topics: list[Topic]) -> bool:
    match direction:
        case IndexDirection.INDEX:
            return True
        case IndexDirection.NO_INDEX:
            return False
        case IndexDirection.AUTO:
            # 現在の条件：「夢」から始まるトピックを除き、トピックが3個以上
            count_topics = [topic for topic in topics if topic.title[0] != "夢"]
            return len(count_topics) >= 3


def _generate_description(topics: list[Topic]) -> str:
    """
    ページ説明文を生成（「夢」から始まらないトピックのトピック名＋本文の合わせて120文字）
    """
    description = ""
    for topic in topics:
        if topic.title[0] == "夢":
            continue
        description += topic.title + " " + "".join(topic.content) + " "
        description = re.sub(r"</?[a-zA-Z0-9][a-zA-Z0-9 '\"-_.@&$%/]+>", "", description)
        description = re.sub(
            r"https?://[a-zA-Z0-9!\?/\+\-_~=;\.,\*&@#$%\(\)'\[\]]+", "", description
        )
        if len(description) >= 120:
            continue
    return description[:120]
