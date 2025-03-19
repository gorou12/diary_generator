from collections import Counter

from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry
from diary_generator.util import utilities

log = logger.get_logger()


def generate(diary_entries: list[DiaryEntry]):
    output_dir = config.FILE_NAMES.OUTPUT_BASE_DIR_NAME
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

    pages, total_pages = utilities.paginate_list(
        sorted_topics, config.PAGINATE.TOPIC_LIST
    )

    for idx, page_items in enumerate(pages):
        page_num = idx + 1
        filename = (
            f"{output_dir}topics_{page_num}.html"
            if page_num > 1
            else f"{output_dir}topics.html"
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
            "should_index": False,
            "description": "ごろうの日記をまとめたサイト。",
            "topics": page_items,
            "popular_topics": popular_topics[:10],
            "pagination": pagination,
        }
        utilities.render_template("topics.html", context, filename)

    log.info("✅ トピック一覧ページ（ページネーション付き）を生成しました！")
