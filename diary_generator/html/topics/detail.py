import os
from collections import defaultdict

from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry
from diary_generator.topic_slug import TopicSlugResolver
from diary_generator.util import utilities

log = logger.get_logger()


def generate(diary_entries: list[DiaryEntry], resolver: TopicSlugResolver):
    topics_root = config.FILE_NAMES.OUTPUT_TOPICS_DIR_NAME
    per_page_dates = config.PAGINATE.TOPIC_DETAIL_DATES

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
    for topic_name, entries in combined_dict.items():
        grouped_by_date = defaultdict(list)
        for date, entry in entries:
            grouped_by_date[date].append(entry)

        # Jinja2用コンテキスト準備
        latest_date = (
            sorted(grouped_by_date.keys(), reverse=True)[0] if grouped_by_date else None
        )

        # 「日付ブロック」単位でページング
        date_blocks = [
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
        ]
        pages, total_pages = utilities.paginate_list(date_blocks, per_page_dates)

        canonical_slug = resolver.slug(topic_name)
        canonical_dir = os.path.join(topics_root, canonical_slug)

        # 1) canonical の topic ページ本体（ページネーションあり）
        for idx, page_items in enumerate(pages):
            page_num = idx + 1

            if page_num == 1:
                out_path = os.path.join(canonical_dir, "index.html")
                page_url = resolver.url(topic_name, 1)
            else:
                out_path = os.path.join(
                    canonical_dir, "page", str(page_num), "index.html"
                )
                page_url = resolver.url(topic_name, page_num)

            # ページネーションリンク
            pagination = ""
            if total_pages > 1:
                if page_num > 1:
                    prev_url = resolver.url(topic_name, page_num - 1)
                    pagination += f'<a href="{prev_url}">« 前へ</a> '
                pagination += f"<span>{page_num}/{total_pages}</span>"
                if page_num < total_pages:
                    next_url = resolver.url(topic_name, page_num + 1)
                    pagination += f' <a href="{next_url}">次へ »</a>'

            context = {
                "title": f"トピック: {topic_name}",
                "should_index": True,
                "description": f"{topic_name}に関する日記。",
                "topic_name": topic_name,
                "initial_month": latest_date[:7] if latest_date else None,
                "entries": page_items,
                "pagination": pagination,
                "canonical_url": page_url,
            }

            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            utilities.render_template("topic.html", context, out_path)

        # 2) 旧URL（topics/<topic_name>.html）は canonical へリダイレクトするスタブとして残す
        legacy_context = {
            "dest_url": resolver.url(topic_name, 1),
        }
        legacy_path = os.path.join(canonical_dir, "index.html")
        utilities.render_template("redirect.html", legacy_context, legacy_path)

        # 3) 手動スラッグが設定された場合は、以前の自動スラッグURLもリダイレクトにする
        auto_slug = resolver.auto_slug(topic_name)
        if auto_slug != canonical_slug:
            auto_dir = os.path.join(topics_root, auto_slug)
            auto_index = os.path.join(auto_dir, "index.html")
            auto_context = {
                "dest_url": resolver.url(topic_name, 1),
            }
            utilities.render_template("redirect.html", auto_context, auto_index)

    log.info(
        "✅ トピック詳細ページ（slug + ページネーション + 旧URLリダイレクト）を生成しました！"
    )
