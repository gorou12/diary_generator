import os
from collections import defaultdict

from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry, Topic
from diary_generator.topic_slug import TopicSlugResolver
from diary_generator.util import utilities

log = logger.get_logger()


def _collect_topic_entries_by_slug(
    diary_entries: list[DiaryEntry],
    resolver: TopicSlugResolver,
) -> tuple[dict[str, list[tuple[str, Topic]]], dict[str, str]]:
    """
    canonical slug ごとに (date, topic) を収集する。
    別名・エイリアスが同一スラッグに解決される場合は同一バケットにマージされる。
    """
    combined_dict: dict[str, list[tuple[str, Topic]]] = defaultdict(list)
    slug_display_fallbacks: dict[str, str] = {}

    for diary_entry in diary_entries:
        date = diary_entry.date
        for topic in diary_entry.topics:
            slug_key = resolver.slug(topic.title)
            slug_display_fallbacks.setdefault(slug_key, topic.title)
            if (date, topic) not in combined_dict[slug_key]:
                combined_dict[slug_key].append((date, topic))
            for hashtag in topic.hashtags:
                sk = resolver.slug(hashtag)
                slug_display_fallbacks.setdefault(sk, hashtag)
                if (date, topic) not in combined_dict[sk]:
                    combined_dict[sk].append((date, topic))
    return combined_dict, slug_display_fallbacks


def _collect_all_raw_labels(diary_entries: list[DiaryEntry]) -> list[str]:
    """旧 URL 用リダイレクトのため、日記に現れるすべての見出し名・ハッシュタグ文字列を集める。"""
    labels: set[str] = set()
    for diary_entry in diary_entries:
        for topic in diary_entry.topics:
            labels.add(topic.title)
            for hashtag in topic.hashtags:
                labels.add(hashtag)
    return sorted(labels)


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
    url_key: str, page_num: int, total_pages: int, resolver: TopicSlugResolver
) -> str:
    if total_pages <= 1:
        return ""

    pagination = ""
    if page_num > 1:
        prev_url = resolver.url_for_slug(url_key, page_num - 1)
        pagination += f'<a href="{prev_url}">« 前へ</a> '
    pagination += f"<span>{page_num}/{total_pages}</span>"
    if page_num < total_pages:
        next_url = resolver.url_for_slug(url_key, page_num + 1)
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
    display_name: str,
    canonical_slug: str,
    latest_date: str | None,
    pages: list[list[dict]],
    total_pages: int,
    topics_root: str,
    resolver: TopicSlugResolver,
) -> None:
    """トピック詳細ページ（正本）を生成する。"""
    canonical_dir = os.path.join(topics_root, canonical_slug)

    for idx, page_items in enumerate(pages):
        page_num = idx + 1
        if page_num == 1:
            out_path = os.path.join(canonical_dir, "index.html")
        else:
            out_path = os.path.join(canonical_dir, "page", str(page_num), "index.html")
        page_url = resolver.url_for_slug(canonical_slug, page_num)

        context = _build_topic_context(
            topic_name=display_name,
            latest_date=latest_date,
            page_items=page_items,
            pagination=_build_pagination_html(
                url_key=canonical_slug,
                page_num=page_num,
                total_pages=total_pages,
                resolver=resolver,
            ),
            page_url=page_url,
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        utilities.render_template("topic.html", context, out_path)


def _render_page1_redirect(
    resolver: TopicSlugResolver,
    topics_root: str,
    canonical_slug: str,
) -> None:
    """同一 slug に対して 1 回だけ: /topics/slug/page/1/ を canonical へ誘導。"""
    dest_url = resolver.url_for_slug(canonical_slug, 1)
    redirect_context = {"dest_url": dest_url}
    auto_page = os.path.join(topics_root, canonical_slug, "page", "1", "index.html")
    os.makedirs(os.path.dirname(auto_page), exist_ok=True)
    utilities.render_template("redirect.html", redirect_context, auto_page)


def _render_legacy_and_auto_redirects_for_label(
    raw_label: str,
    resolver: TopicSlugResolver,
    topics_root: str,
) -> None:
    """
    日記に現れる各ラベルごとに: 旧 topics/<ラベル>.html と旧自動スラッグ URL を canonical へ誘導。
    """
    canonical_slug = resolver.slug(raw_label)
    dest_url = resolver.url_for_slug(canonical_slug, 1)
    redirect_context = {"dest_url": dest_url}

    legacy_path = os.path.join(topics_root, f"{raw_label}.html")
    os.makedirs(os.path.dirname(legacy_path), exist_ok=True)
    utilities.render_template("redirect.html", redirect_context, legacy_path)

    auto_slug = resolver.auto_slug(raw_label)
    if auto_slug != canonical_slug:
        auto_index = os.path.join(topics_root, auto_slug, "index.html")
        os.makedirs(os.path.dirname(auto_index), exist_ok=True)
        utilities.render_template("redirect.html", redirect_context, auto_index)


def generate(diary_entries: list[DiaryEntry], resolver: TopicSlugResolver):
    topics_root = config.FILE_NAMES.OUTPUT_TOPICS_DIR_NAME
    per_page_dates = config.PAGINATE.TOPIC_DETAIL_DATES

    topic_entries, slug_display_fallbacks = _collect_topic_entries_by_slug(
        diary_entries, resolver
    )

    for canonical_slug, entries in topic_entries.items():
        display_name = resolver.display_name_for_slug(
            canonical_slug, fallback=slug_display_fallbacks.get(canonical_slug)
        )
        grouped_by_date = _group_entries_by_date(entries)
        sorted_dates = sorted(grouped_by_date.keys(), reverse=True)
        latest_date = sorted_dates[0] if sorted_dates else None

        date_blocks = _build_date_blocks(grouped_by_date)
        pages, total_pages = utilities.paginate_list(date_blocks, per_page_dates)

        _render_canonical_pages(
            display_name=display_name,
            canonical_slug=canonical_slug,
            latest_date=latest_date,
            pages=pages,
            total_pages=total_pages,
            topics_root=topics_root,
            resolver=resolver,
        )
        _render_page1_redirect(resolver, topics_root, canonical_slug)

    for raw_label in _collect_all_raw_labels(diary_entries):
        _render_legacy_and_auto_redirects_for_label(raw_label, resolver, topics_root)

    log.info(
        "✅ トピック詳細ページ（slug + ページネーション + 旧URLリダイレクト）を生成しました！"
    )
