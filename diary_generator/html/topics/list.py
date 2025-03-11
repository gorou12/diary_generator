from collections import Counter

from ... import utils
from ...models import Config, DiaryEntry


def generate(diary_entries: list[DiaryEntry], config: Config):
    topic_counter = Counter()
    for diary_entry in diary_entries:
        for topic in diary_entry.topics:
            topic_counter[topic.title] += 1
            for hashtag in topic.hashtags:
                topic_counter[hashtag] += 1

    sorted_topics = topic_counter.most_common()
    popular_topics = [
        tpl for tpl in sorted_topics if tpl[1] >= 2
    ]  # Counterが2以上のものだけ

    pages, total_pages = utils.paginate_list(sorted_topics, config.topiclist.paginate)

    for idx, page_items in enumerate(pages):
        page_num = idx + 1
        filename = (
            f"output/topics_{page_num}.html" if page_num > 1 else "output/topics.html"
        )

        # ページネーションリンク作成
        pagination = ""
        if page_num > 1:
            prev_link = (
                "topics.html" if page_num == 2 else f"topics_{page_num - 1}.html"
            )
            pagination += f'<a href="{prev_link}">« 前へ</a> '
        if page_num < total_pages:
            next_link = f"topics_{page_num + 1}.html"
            pagination += f'<a href="{next_link}">次へ »</a>'

        # Jinja2 context
        context = {
            "title": "トピック一覧",
            "topics": page_items,
            "popular_topics": popular_topics[:10],
            "pagination": pagination,
            "sidebar_content": "",
        }
        utils.render_template("topics.html", context, filename)

    print("✅ トピック一覧ページ（ページネーション付き）を生成しました！")
