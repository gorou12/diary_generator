from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry, IndexDirection, Topic
from diary_generator.util import utilities

log = logger.get_logger()


def generate(diary_entries: list[DiaryEntry]):
    dates_dir = config.FILE_NAMES.OUTPUT_DATES_DIR_NAME
    dates_nav = _create_dates_nav(diary_entries)

    for diary_entry in diary_entries:
        date = diary_entry.date
        topics = diary_entry.topics
        should_index = _judge_index(diary_entry.index_direction, topics)
        context = {
            "title": f"日記 - {date}",
            "should_index": should_index,
            "date": date,
            "topics": topics,  # [{'title': ..., 'content': [...], 'hashtags': [...]}, ...]
            "prev_date": dates_nav[date]["prev"],
            "next_date": dates_nav[date]["next"],
            "newest_date": dates_nav[date]["newest"],
        }
        output_file = f"{dates_dir}{date}.html"
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
            # 現在の条件：トピックが4個以上
            return len(topics) >= 4
