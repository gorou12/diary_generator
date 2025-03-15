from collections import defaultdict

from diary_generator.config.configuration import config
from diary_generator.models import DiaryEntry
from diary_generator.util import utilities


def generate(diary_entries: list[DiaryEntry]):
    topics_dir = config.FILE_NAMES.OUTPUT_TOPICS_DIR_NAME
    combined_dict = defaultdict(list)

    # トピック・ハッシュタグの収集
    for diary_entry in diary_entries:
        date = diary_entry.date
        for topic in diary_entry.topics:
            combined_dict[topic.title].append((date, topic))
            for hashtag in topic.hashtags:
                # トピック名とタグが同じものがついているもの以外を追加
                if (date, topic) not in combined_dict[hashtag]:
                    combined_dict[hashtag].append((date, topic))

    # 各トピックごとに生成
    for topic, entries in combined_dict.items():
        grouped_by_date = defaultdict(list)
        for date, entry in entries:
            grouped_by_date[date].append(entry)

        # Jinja2用コンテキスト準備
        context = {
            "title": f"トピック: {topic}",
            "topic_name": topic,
            "entries": [
                {
                    "date": f"{date[:4]}年{date[5:7]}月{date[8:10]}日",
                    "date_raw": date,
                    "entries": [
                        {
                            "title": entry.title,
                            "hashtags": entry.hashtags,
                            "content": entry.content,
                            "content_html": entry.content_html,
                        }
                        for entry in grouped_by_date[date]
                    ],
                }
                for date in sorted(grouped_by_date.keys(), reverse=True)
            ],
            "sidebar_content": "",  # 人気ランキングなど入れたい場合はここに
        }

        # ファイル出力
        output_file = f"{topics_dir}{topic}.html"
        utilities.render_template("topic.html", context, output_file)

    print("✅ トピックページ（ハッシュタグ含む）を生成しました！（Jinja2版）")
