import os

from ... import utils
from ...models import Config, DiaryEntry


def generate(diary_entries: list[DiaryEntry], config: Config):
    os.makedirs("output/dates", exist_ok=True)

    dates_nav = _create_dates_nav(diary_entries)

    for diary_entry in diary_entries:
        date = diary_entry.date
        topics = diary_entry.topics
        context = {
            "title": f"日記 - {date}",
            "date": date,
            "topics": topics,  # [{'title': ..., 'content': [...], 'hashtags': [...]}, ...]
            "prev_date": dates_nav[date]["prev"],
            "next_date": dates_nav[date]["next"],
            "newest_date": dates_nav[date]["newest"],
            "sidebar_content": "",  # 必要ならランキングなど入れる
        }
        output_file = f"output/dates/{date}.html"
        utils.render_template("date.html", context, output_file)
    print("✅ 日付ページを生成しました！")


def _create_dates_nav(diary_entries: list[DiaryEntry]) -> dict:
    sorted_dates = sorted([d.date for d in diary_entries])
    newest_date = sorted_dates[-1]
    dates_nav = {}
    for i, date in enumerate(sorted_dates):
        prev_date = sorted_dates[i - 1] if i > 0 else None
        next_date = sorted_dates[i + 1] if i < (len(sorted_dates) - 1) else None
        dates_nav[date] = {"prev": prev_date, "next": next_date, "newest": newest_date}

    return dates_nav
