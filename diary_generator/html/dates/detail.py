import os

from ... import utils
from ...models import Config, DiaryEntry


def generate(diary_entries: list[DiaryEntry], config: Config):
    os.makedirs("output/dates", exist_ok=True)

    for diary_entry in diary_entries:
        date = diary_entry.date
        topics = diary_entry.topics
        context = {
            "title": f"日記 - {date}",
            "date": date,
            "topics": topics,  # [{'title': ..., 'content': [...], 'hashtags': [...]}, ...]
            "sidebar_content": "",  # 必要ならランキングなど入れる
        }
        output_file = f"output/dates/{date}.html"
        utils.render_template("date.html", context, output_file)
    print("✅ 日付ページを生成しました！")
