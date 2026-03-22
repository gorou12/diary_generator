import os
from collections import defaultdict

from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry, Topic
from diary_generator.topic_slug import TopicSlugResolver
from diary_generator.util import utilities

log = logger.get_logger()


def _collect_topic_entries(
    diary_entries: list[DiaryEntry],
) -> dict[str, list[tuple[str, Topic]]]:
    combined_dict: dict[str, list[tuple[str, Topic]]] = defaultdict(list)

    # トピック名 + ハッシュタグ名ごとに (date, topic) を収集
    for diary_entry in diary_entries:
        date = diary_entry.date
        for topic in diary_entry.topics:
            combined_dict[topic.title].append((date, topic))
            for hashtag in topic.hashtags:
                # トピック名とタグが同じものがついているもの以外を追加
                if (date, topic) not in combined_dict[hashtag]:
                    combined_dict[hashtag].append((date, topic))
    return combined_dict


def _group_entries_by_date(entries: list[tuple[str, Topic]]) -> dict[str, list[Topic]]:
    grouped_by_date: dict[str, list[Topic]] = defaultdict(list)
    for date, entry in entries:
        grouped_by_date[date].append(entry)
    return grouped_by_date


def _build_date_blocks(grouped_by_date: dict[str, list[Topic]]) -> list[dict]:
    return [
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


def _build_pagination_html(
    topic_name: str, page_num: int, total_pages: int, resolver: TopicSlugResolver
) -> str:
    if total_pages <= 1:
        return ""

    pagination = ""
    if page_num > 1:
        prev_url = resolver.url(topic_name, page_num - 1)
        pagination += f'<a href="{prev_url}">« 前へ</a> '
    pagination += f"<span>{page_num}/{total_pages}</span>"
    if page_num < total_pages:
        next_url = resolver.url(topic_name, page_num + 1)
        pagination += f' <a href="{next_url}">次へ »</a>'
    return pagination


def _build_topic_context(
    topic_name: str,
    latest_date: str | None,
    page_items: list[dict],
    pagination: str,
    page_url: str,
) -> dict:
    return {
        "title": f"トピック: {topic_name}",
        "should_index": True,
        "description": f"{topic_name}に関する日記。",
        "topic_name": topic_name,
        "initial_month": latest_date[:7] if latest_date else None,
        "entries": page_items,
        "pagination": pagination,
        "canonical_url": page_url,
    }


def _render_canonical_pages(
    topic_name: str,
    latest_date: str | None,
    pages: list[list[dict]],
    total_pages: int,
    topics_root: str,
    resolver: TopicSlugResolver,
) -> str:
    """
    トピック詳細ページ（正本）を生成する。
    """
    canonical_slug = resolver.slug(topic_name)
    canonical_dir = os.path.join(topics_root, canonical_slug)

    for idx, page_items in enumerate(pages):
        page_num = idx + 1
        if page_num == 1:
            out_path = os.path.join(canonical_dir, "index.html")
            page_url = resolver.url(topic_name, 1)
        else:
            out_path = os.path.join(canonical_dir, "page", str(page_num), "index.html")
            page_url = resolver.url(topic_name, page_num)

        context = _build_topic_context(
            topic_name=topic_name,
            latest_date=latest_date,
            page_items=page_items,
            pagination=_build_pagination_html(
                topic_name=topic_name,
                page_num=page_num,
                total_pages=total_pages,
                resolver=resolver,
            ),
            page_url=page_url,
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        utilities.render_template("topic.html", context, out_path)

    return canonical_slug


def _render_redirects(
    topic_name: str,
    topics_root: str,
    resolver: TopicSlugResolver,
    canonical_slug: str,
):
    """
    トピック詳細ページ（リダイレクト用）を生成する。
    """
    redirect_context = {"dest_url": resolver.url(topic_name, 1)}

    # 旧URL（topics/<topic_name>.html）から canonical に誘導
    legacy_path = os.path.join(topics_root, f"{topic_name}.html")
    os.makedirs(os.path.dirname(legacy_path), exist_ok=True)
    utilities.render_template("redirect.html", redirect_context, legacy_path)

    # 手動スラッグ設定時、旧自動スラッグURLも canonical に誘導
    auto_slug = resolver.auto_slug(topic_name)
    if auto_slug != canonical_slug:
        auto_index = os.path.join(topics_root, auto_slug, "index.html")
        os.makedirs(os.path.dirname(auto_index), exist_ok=True)
        utilities.render_template("redirect.html", redirect_context, auto_index)

    # /topics/slug/page/1/index.html から canonical に誘導
    auto_page = os.path.join(topics_root, canonical_slug, "page", "1", "index.html")
    os.makedirs(os.path.dirname(auto_page), exist_ok=True)
    utilities.render_template("redirect.html", redirect_context, auto_page)


def generate(diary_entries: list[DiaryEntry], resolver: TopicSlugResolver):
    topics_root = config.FILE_NAMES.OUTPUT_TOPICS_DIR_NAME
    per_page_dates = config.PAGINATE.TOPIC_DETAIL_DATES

    topic_entries = _collect_topic_entries(diary_entries)

    for topic_name, entries in topic_entries.items():
        grouped_by_date = _group_entries_by_date(entries)
        sorted_dates = sorted(grouped_by_date.keys(), reverse=True)
        latest_date = sorted_dates[0] if sorted_dates else None

        date_blocks = _build_date_blocks(grouped_by_date)
        pages, total_pages = utilities.paginate_list(date_blocks, per_page_dates)

        canonical_slug = _render_canonical_pages(
            topic_name=topic_name,
            latest_date=latest_date,
            pages=pages,
            total_pages=total_pages,
            topics_root=topics_root,
            resolver=resolver,
        )
        _render_redirects(
            topic_name=topic_name,
            topics_root=topics_root,
            resolver=resolver,
            canonical_slug=canonical_slug,
        )

    log.info(
        "✅ トピック詳細ページ（slug + ページネーション + 旧URLリダイレクト）を生成しました！"
    )
