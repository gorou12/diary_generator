import os
from collections import defaultdict

from ... import utils
from ...models import Config, DiaryEntry


def generate(diary_entries: list[DiaryEntry], config: Config):
    os.makedirs("output/topics", exist_ok=True)

    topic_dict = defaultdict(list)
    hashtag_dict = defaultdict(list)

    # トピック・ハッシュタグの収集
    for diary_entry in diary_entries:
        date = diary_entry.date
        for topic in diary_entry.topics:
            topic_dict[topic.title].append((date, topic))
            for hashtag in topic.hashtags:
                hashtag_dict[hashtag].append((date, topic))

    # トピック＋ハッシュタグ統合
    combined_dict = {**topic_dict, **hashtag_dict}

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
                        }
                        for entry in grouped_by_date[date]
                    ],
                }
                for date in sorted(grouped_by_date.keys(), reverse=True)
            ],
            "sidebar_content": "",  # 人気ランキングなど入れたい場合はここに
        }

        # ファイル出力
        output_file = f"output/topics/{topic}.html"
        utils.render_template("topic.html", context, output_file)

    print("✅ トピックページ（ハッシュタグ含む）を生成しました！（Jinja2版）")
