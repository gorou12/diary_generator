import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import unquote, urlsplit

import pytest
from bs4 import BeautifulSoup

from diary_generator import contents, filemaintenance, html
from diary_generator.config.configuration import config
from diary_generator.json import calendar, search
from diary_generator.models import DiaryEntry, IndexDirection, Topic
from diary_generator.topic_slugs.normalize import normalize_topic_key
from diary_generator.topic_slugs.resolve import TopicSlugResolver
from diary_generator.util import utilities
from tests.helpers import block, notion_children_response

JST = timezone(timedelta(hours=9))


@dataclass
class GeneratedSite:
    output_dir: Path
    entries: list[DiaryEntry]
    resolver: TopicSlugResolver


@pytest.fixture()
def generated_site(tmp_path, monkeypatch):
    output_dir = tmp_path / "output"
    cache_dir = tmp_path / "cache"
    for path in [
        output_dir,
        output_dir / "dates",
        output_dir / "topics",
        output_dir / "src",
        output_dir / "json",
        output_dir / "images",
        output_dir / "thumbnails" / "small",
        output_dir / "thumbnails" / "medium",
        output_dir / "thumbnails" / "large",
        cache_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    original_file_names = config.FILE_NAMES
    original_paginate = config.PAGINATE
    original_topic_url_fn = utilities._topic_url_fn
    object.__setattr__(
        config,
        "FILE_NAMES",
        SimpleNamespace(
            CACHE_DIR_NAME=f"{cache_dir}{os.sep}",
            CACHE_DIARY_INDEX_PATH=str(cache_dir / "diary_index.json"),
            CACHE_DIARY_DETAIL_PATH=str(cache_dir / "diary_detail.json"),
            CACHE_OGP_PATH=str(cache_dir / "ogp.json"),
            CACHE_TWITTER_PATH=str(cache_dir / "twitter.json"),
            CACHE_TOPIC_SLUGS_PATH=str(cache_dir / "topic_slugs.json"),
            STATIC_FILES_DIR_NAME="static/",
            OUTPUT_BASE_DIR_NAME=f"{output_dir}{os.sep}",
            OUTPUT_DATES_DIR_NAME=f"{output_dir / 'dates'}{os.sep}",
            OUTPUT_TOPICS_DIR_NAME=f"{output_dir / 'topics'}{os.sep}",
            OUTPUT_STATIC_FILES_DIR_NAME=f"{output_dir / 'src'}{os.sep}",
            OUTPUT_IMAGE_DIR_NAME=f"{output_dir / 'images'}{os.sep}",
            OUTPUT_THUMBNAILS_DIR_NAME=f"{output_dir / 'thumbnails'}{os.sep}",
            OUTPUT_THUMBNAILS_SMALL_DIR_NAME=f"{output_dir / 'thumbnails' / 'small'}{os.sep}",
            OUTPUT_THUMBNAILS_MEDIUM_DIR_NAME=f"{output_dir / 'thumbnails' / 'medium'}{os.sep}",
            OUTPUT_THUMBNAILS_LARGE_DIR_NAME=f"{output_dir / 'thumbnails' / 'large'}{os.sep}",
            OUTPUT_JSON_DIR_NAME=f"{output_dir / 'json'}{os.sep}",
        ),
    )
    object.__setattr__(
        config,
        "PAGINATE",
        SimpleNamespace(
            INDEX_TOPICS=2,
            TOPIC_LIST=3,
            DATE_LIST=2,
            TOPIC_DETAIL_DATES=1,
            DATE_DETAIL_TOPICS=20,
        ),
    )

    resolver = fixed_resolver()
    utilities.set_topic_url_fn(resolver.url_for_title)

    try:
        entries = diary_entries(monkeypatch)
        filemaintenance.copy_static_files()
        html.index.generate(entries)
        html.dates.list.generate(entries)
        html.dates.detail.generate(entries)
        html.topics.list.generate(entries)
        html.topics.detail.generate(entries, resolver)
        html.search.generate()
        search.generate(entries)
        calendar.generate(entries)
        yield GeneratedSite(output_dir=output_dir, entries=entries, resolver=resolver)
    finally:
        object.__setattr__(config, "FILE_NAMES", original_file_names)
        object.__setattr__(config, "PAGINATE", original_paginate)
        utilities.set_topic_url_fn(original_topic_url_fn)


def fixed_resolver() -> TopicSlugResolver:
    label_to_slug = {
        "買い物 #生活": "shopping",
        "生活": "life",
        "食事": "meal",
        "リンク": "linked-text",
        "画像": "image-block",
        "旧トピック名": "renamed-topic",
        "タグだけ": "tag-only",
        "新タグ": "new-tag",
        "散歩": "walk",
        "料理": "cooking",
        "読書": "reading",
        "本": "book",
    }
    manual = {normalize_topic_key(k): v for k, v in label_to_slug.items()}
    slug_to_display = {v: k for k, v in label_to_slug.items()}
    return TopicSlugResolver(manual, slug_to_display)


def diary_entries(monkeypatch) -> list[DiaryEntry]:
    parsed_topics, has_pending = public_topics_from_notion_blocks(monkeypatch)
    assert has_pending is True

    return [
        DiaryEntry(
            date="2026-01-15",
            date_jpn="2026年01月15日",
            index_direction=IndexDirection.INDEX,
            topics=[
                *parsed_topics,
                topic(
                    "リンク",
                    "topic-link",
                    ["参考資料を読んだ"],
                    [
                        '参考: <a href="https://example.com/ref" target="_blank">資料</a>'
                    ],
                ),
                topic(
                    "画像",
                    "topic-image",
                    ["写真を載せた"],
                    [
                        '<img class="embedimg" src="/images/public-photo.jpg" alt="写真">'
                    ],
                ),
                topic("旧トピック名", "topic-legacy", ["旧URLから新URLへ"]),
            ],
        ),
        DiaryEntry(
            date="2026-01-14",
            date_jpn="2026年01月14日",
            index_direction=IndexDirection.INDEX,
            topics=[
                topic(
                    "買い物 #生活",
                    "topic-shopping-2",
                    ["翌日も買い物した"],
                    hashtags=["生活"],
                ),
                topic(
                    "タグだけ",
                    "topic-tag-only",
                    ["本文変更なしでタグだけ追加された"],
                    hashtags=["新タグ"],
                ),
            ],
        ),
        DiaryEntry(
            date="2026-01-13",
            date_jpn="2026年01月13日",
            index_direction=IndexDirection.INDEX,
            topics=[topic("散歩", "topic-walk", ["公園を歩いた"])],
        ),
        DiaryEntry(
            date="2026-01-12",
            date_jpn="2026年01月12日",
            index_direction=IndexDirection.INDEX,
            topics=[
                topic("料理", "topic-cooking", ["味噌汁を作った"], hashtags=["食事"])
            ],
        ),
        DiaryEntry(
            date="2026-01-11",
            date_jpn="2026年01月11日",
            index_direction=IndexDirection.INDEX,
            topics=[topic("読書", "topic-reading", ["本を読んだ"], hashtags=["本"])],
        ),
    ]


def public_topics_from_notion_blocks(monkeypatch) -> tuple[list[Topic], bool]:
    now = datetime(2026, 1, 15, 12, 0, tzinfo=JST)
    old = (now - timedelta(minutes=10)).isoformat()
    pending = now.isoformat()
    blocks = [
        block(
            "heading_3", "買い物 #生活", block_id="topic-shopping", last_edited_time=old
        ),
        block("paragraph", "スーパーで野菜を買った", last_edited_time=old),
        block("paragraph", "", last_edited_time=old),
        block("paragraph", "夕飯の材料を選んだ", last_edited_time=old),
        block("paragraph", "#生活 #食事", last_edited_time=old),
        block("paragraph", "", last_edited_time=old),
        block("heading_3", "秘密", block_id="topic-private", last_edited_time=old),
        block("paragraph", "秘密本文", last_edited_time=old),
        block("paragraph", "#非公開", last_edited_time=old),
        {
            "id": "private-image",
            "type": "image",
            "last_edited_time": old,
            "image": {
                "type": "external",
                "external": {"url": "https://example.com/private.jpg"},
            },
        },
        block(
            "heading_3", "編集中", block_id="topic-pending", last_edited_time=pending
        ),
        block("paragraph", "まだ出さない", last_edited_time=pending),
    ]
    monkeypatch.setattr(
        contents.notion_api,
        "get_block_children",
        lambda _page_id, start_cursor=None: notion_children_response(blocks),
    )

    raw_topics, has_pending = contents._fetch_diary_page("page-2026-01-15", now)
    topics = [
        Topic(
            title=raw["title"],
            id=raw["topic_id"],
            content=contents._build_topic_content(raw),
            content_html=contents._build_topic_content(raw),
            hashtags=raw["tags"],
        )
        for raw in raw_topics
    ]
    return topics, has_pending


def topic(
    title: str,
    topic_id: str,
    content: list[str],
    content_html: list[str] | None = None,
    *,
    hashtags: list[str] | None = None,
) -> Topic:
    return Topic(
        title=title,
        id=topic_id,
        content=content,
        content_html=content_html or content,
        hashtags=hashtags or [],
    )


def soup(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def text(path: Path) -> str:
    return soup(path).get_text(" ", strip=True)


def all_html(output_dir: Path) -> list[Path]:
    return sorted(output_dir.glob("**/*.html"))


def assert_contains(path: Path, *needles: str) -> None:
    page_text = text(path)
    for needle in needles:
        assert needle in page_text


def assert_not_contains_any(path: Path, *needles: str) -> None:
    page_html = path.read_text(encoding="utf-8")
    page_text = soup(path).get_text(" ", strip=True)
    for needle in needles:
        assert needle not in page_html
        assert needle not in page_text


def test_major_html_files_are_generated(generated_site):
    """
    主要HTMLファイルが生成される。
    index.html、dates.html、topics.html、日付ページ、トピックslugページを確認する。
    """
    out = generated_site.output_dir

    assert (out / "index.html").exists()
    assert (out / "dates.html").exists()
    assert (out / "topics.html").exists()
    assert (out / "dates" / "2026-01-15.html").exists()
    assert (out / "topics" / "shopping" / "index.html").exists()


def test_all_html_has_minimum_document_structure(generated_site):
    """
    全HTMLが最低限のHTML構造を持つ。
    html、body、title が存在し、空HTMLではないことを確認する。
    """
    for path in all_html(generated_site.output_dir):
        parsed = soup(path)
        assert path.read_text(encoding="utf-8").strip()
        assert parsed.html is not None
        assert parsed.body is not None
        assert parsed.title is not None


def test_top_page_shows_public_topics_and_links(generated_site):
    """
    トップページに公開トピックが表示される。
    日付、トピックタイトル、本文、日付ページ・トピックページへのリンクを確認する。
    """
    parsed = soup(generated_site.output_dir / "index.html")
    page_text = parsed.get_text(" ", strip=True)

    assert "2026-01-15" in page_text
    assert "買い物 #生活" in page_text
    assert "スーパーで野菜を買った" in page_text
    assert parsed.find("a", href="/dates/2026-01-15.html") is not None
    assert parsed.find("a", href="/topics/shopping/") is not None


def test_date_page_shows_only_topics_for_that_date(generated_site):
    """
    日付ページにその日のトピックだけが表示される。
    対象日のトピックが表示され、別日のトピックが混ざらないことを確認する。
    """
    date_page = generated_site.output_dir / "dates" / "2026-01-15.html"

    assert_contains(date_page, "買い物 #生活", "リンク", "画像", "旧トピック名")
    assert_not_contains_any(date_page, "翌日も買い物した", "散歩", "味噌汁")


def test_topic_page_shows_only_target_topic_across_dates(generated_site):
    """
    トピックページに対象トピックだけが表示される。
    複数日の同一トピック、日付ページへのリンク、関係ないトピックの混入なしを確認する。
    """
    topic_page = generated_site.output_dir / "topics" / "shopping" / "index.html"
    parsed = soup(topic_page)

    assert_contains(topic_page, "買い物 #生活", "スーパーで野菜を買った")
    assert parsed.find("a", href="/dates/2026-01-15.html") is not None
    assert_not_contains_any(topic_page, "リンク", "画像", "散歩", "味噌汁")

    page2 = (
        generated_site.output_dir / "topics" / "shopping" / "page" / "2" / "index.html"
    )
    assert_contains(page2, "買い物 #生活", "翌日も買い物した")
    assert soup(page2).find("a", href="/dates/2026-01-14.html") is not None


def test_private_and_pending_topics_never_appear_in_html(generated_site):
    """
    非公開内容と pending トピックが全HTMLに出ない。
    非公開タイトル・本文・タグ・リンクと、編集後5分未満の内容が各ページに出ないことを確認する。
    """
    forbidden = [
        "秘密",
        "秘密本文",
        "#非公開",
        "非公開",
        "private.jpg",
        "編集中",
        "まだ出さない",
    ]
    for path in all_html(generated_site.output_dir):
        assert_not_contains_any(path, *forbidden)
        assert not any(
            "private" in (a.get("href") or "") or "pending" in (a.get("href") or "")
            for a in soup(path).find_all("a", href=True)
        )

    topics_text = text(generated_site.output_dir / "topics.html")
    dates_text = text(generated_site.output_dir / "dates.html")
    assert "編集中" not in topics_text
    assert "まだ出さない" not in dates_text


def test_internal_links_are_not_broken(generated_site):
    """
    内部リンク切れがない。
    output/**/*.html の a[href] を走査し、外部リンクやフラグメントを除く内部リンク先の存在を確認する。
    """
    missing = []
    for path in all_html(generated_site.output_dir):
        for anchor in soup(path).find_all("a", href=True):
            href = anchor["href"]
            if is_external_or_fragment(href):
                continue
            target = resolve_internal_href(generated_site.output_dir, path, href)
            if not target.exists():
                missing.append(
                    (path.relative_to(generated_site.output_dir), href, target)
                )

    assert missing == []


def is_external_or_fragment(href: str) -> bool:
    parsed = urlsplit(href)
    return (
        bool(parsed.scheme and parsed.scheme not in {"", "file"})
        or href.startswith("#")
        or href.startswith("mailto:")
        or href.startswith("tel:")
    )


def resolve_internal_href(output_dir: Path, current_file: Path, href: str) -> Path:
    parsed = urlsplit(href)
    clean = unquote(parsed.path)
    if clean.startswith("/"):
        target = output_dir / clean.lstrip("/")
    else:
        target = current_file.parent / clean
    if clean.endswith("/"):
        target = target / "index.html"
    return target


def test_topics_and_dates_lists_show_only_public_targets(generated_site):
    """
    topics.html と dates.html に公開対象だけが表示される。
    公開トピック・公開日付へのリンクがあり、非公開・pending・公開対象のない日付が出ないことを確認する。
    """
    topics_page = soup(generated_site.output_dir / "topics.html")
    dates_page = soup(generated_site.output_dir / "dates.html")

    assert topics_page.find("a", href="/topics/shopping/") is not None
    assert topics_page.find("a", href="/topics/life/") is not None
    assert "秘密" not in topics_page.get_text(" ", strip=True)
    assert "編集中" not in topics_page.get_text(" ", strip=True)
    assert "非公開" not in topics_page.get_text(" ", strip=True)

    assert dates_page.find("a", href="/dates/2026-01-15.html") is not None
    assert "2026-01-10" not in dates_page.get_text(" ", strip=True)


def test_hashtag_pages_include_only_tagged_topics(generated_site):
    """
    ハッシュタグページにタグ付きトピックが表示される。
    タグページ生成、タグ付きのみの表示、本文変更なしでタグだけ追加されたトピックの反映を確認する。
    """
    life_page = generated_site.output_dir / "topics" / "life" / "index.html"
    new_tag_page = generated_site.output_dir / "topics" / "new-tag" / "index.html"

    assert life_page.exists()
    assert_contains(life_page, "買い物 #生活", "スーパーで野菜を買った")
    assert_not_contains_any(life_page, "リンク", "画像", "散歩")

    assert new_tag_page.exists()
    assert_contains(new_tag_page, "タグだけ", "本文変更なしでタグだけ追加された")
    assert_not_contains_any(new_tag_page, "買い物 #生活", "散歩")


def test_private_hashtag_page_is_not_generated_or_linked(generated_site):
    """
    #非公開 タグページが生成されない。
    topics.html や全HTMLに #非公開 への表示・リンクが存在しないことを確認する。
    """
    out = generated_site.output_dir

    assert not (out / "topics" / "非公開.html").exists()
    assert "非公開" not in text(out / "topics.html")
    for path in all_html(out):
        assert not any(
            "非公開" in (a.get("href") or "") for a in soup(path).find_all("a")
        )


def test_heading_hashtag_tag_paragraph_and_empty_paragraph_rendering(generated_site):
    """
    見出し内タグ、タグ段落、空段落のHTML反映を確認する。
    見出し内 #生活 のタグ化、タグだけ段落の本文非表示、本文途中の空段落保持、末尾空段落の除外を確認する。
    """
    page = generated_site.output_dir / "dates" / "2026-01-15.html"
    parsed = soup(page)
    content = parsed.find("div", class_="content")

    assert "買い物 #生活" in parsed.get_text(" ", strip=True)
    assert parsed.find("a", href="/topics/life/") is not None
    assert "#生活 #食事" not in parsed.get_text("\n", strip=True)
    assert (
        content.find("p", string=lambda value: value and "#生活 #食事" in value) is None
    )

    paragraphs = content.find_all("p")
    assert any(
        p.find("br") is not None and not p.get_text(strip=True) for p in paragraphs
    )
    assert paragraphs[-1].get_text(strip=True) == "夕飯の材料を選んだ"


def test_linked_text_and_image_blocks_render(generated_site):
    """
    リンク付きテキストと画像ブロックがHTMLに表示される。
    aタグのhrefとリンクテキスト、imgタグのsrc、非公開トピック内画像の非表示を確認する。
    """
    page = generated_site.output_dir / "dates" / "2026-01-15.html"
    parsed = soup(page)

    link = parsed.find("a", href="https://example.com/ref")
    assert link is not None
    assert link.get_text(strip=True) == "資料"

    image = parsed.find("img", src=True)
    assert image is not None
    assert image["src"]
    assert "private.jpg" not in page.read_text(encoding="utf-8")


def generate_date_pages(tmp_path, monkeypatch, entries, per_page_topics):
    output_dir = tmp_path / "date-output"
    (output_dir / "dates").mkdir(parents=True, exist_ok=True)
    original_file_names = config.FILE_NAMES
    original_paginate = config.PAGINATE
    object.__setattr__(
        config,
        "FILE_NAMES",
        SimpleNamespace(
            **{
                **getattr(original_file_names, "__dict__", {}),
                "OUTPUT_DATES_DIR_NAME": f"{output_dir / 'dates'}{os.sep}",
            }
        ),
    )
    object.__setattr__(
        config,
        "PAGINATE",
        SimpleNamespace(
            **{
                **getattr(original_paginate, "__dict__", {}),
                "DATE_DETAIL_TOPICS": per_page_topics,
            }
        ),
    )
    try:
        html.dates.detail.generate(entries)
    finally:
        object.__setattr__(config, "FILE_NAMES", original_file_names)
        object.__setattr__(config, "PAGINATE", original_paginate)
    return output_dir


def test_date_detail_without_pagination_keeps_legacy_url_and_hides_pagination(
    generated_site,
):
    """
    日付詳細が1ページに収まる場合は従来URLだけを生成し、ページネーションを表示しない。
    """
    out = generated_site.output_dir
    page = soup(out / "dates" / "2026-01-15.html")

    assert (out / "dates" / "2026-01-15.html").exists()
    assert not (out / "dates" / "2026-01-15" / "page" / "2" / "index.html").exists()
    assert page.select_one(".pagination") is None
    assert page.find("link", rel="canonical")["href"] == "/dates/2026-01-15.html"


def test_date_detail_pagination_splits_topics_and_preserves_order(
    tmp_path, monkeypatch
):
    """
    日付詳細のトピックを設定件数ごとに分割し、重複・欠落なく元の順序で表示する。
    """
    entries = [
        DiaryEntry(
            date="2026-07-12",
            date_jpn="2026年07月12日",
            index_direction=IndexDirection.INDEX,
            topics=[
                topic(f"トピック{i}", f"topic-{i}", [f"本文{i}"]) for i in range(1, 5)
            ],
        )
    ]
    out = generate_date_pages(tmp_path, monkeypatch, entries, per_page_topics=3)

    page1_path = out / "dates" / "2026-07-12.html"
    page2_path = out / "dates" / "2026-07-12" / "page" / "2" / "index.html"
    assert page1_path.exists()
    assert page2_path.exists()

    page1_topics = [
        h3.get_text(" ", strip=True).split()[0]
        for h3 in soup(page1_path).select(".topic h3")
    ]
    page2_topics = [
        h3.get_text(" ", strip=True).split()[0]
        for h3 in soup(page2_path).select(".topic h3")
    ]
    assert page1_topics == ["トピック1", "トピック2", "トピック3"]
    assert page2_topics == ["トピック4"]
    assert page1_topics + page2_topics == [
        "トピック1",
        "トピック2",
        "トピック3",
        "トピック4",
    ]


def test_date_detail_pagination_navigation_and_canonical(tmp_path, monkeypatch):
    """
    日付詳細のページネーション表示、リンク、canonical、日付間ナビゲーションが正しい。
    """
    entries = [
        DiaryEntry(
            date="2026-07-11",
            date_jpn="2026年07月11日",
            index_direction=IndexDirection.INDEX,
            topics=[topic("前日", "prev", ["前日本文"])],
        ),
        DiaryEntry(
            date="2026-07-12",
            date_jpn="2026年07月12日",
            index_direction=IndexDirection.INDEX,
            topics=[
                topic(f"トピック{i}", f"topic-{i}", [f"本文{i}"]) for i in range(1, 5)
            ],
        ),
        DiaryEntry(
            date="2026-07-13",
            date_jpn="2026年07月13日",
            index_direction=IndexDirection.INDEX,
            topics=[topic("翌日", "next", ["翌日本文"])],
        ),
    ]
    out = generate_date_pages(tmp_path, monkeypatch, entries, per_page_topics=1)
    pages = [
        soup(out / "dates" / "2026-07-12.html"),
        soup(out / "dates" / "2026-07-12" / "page" / "2" / "index.html"),
        soup(out / "dates" / "2026-07-12" / "page" / "4" / "index.html"),
    ]

    page1_pagination = pages[0].select_one(".pagination")
    page2_pagination = pages[1].select_one(".pagination")
    page4_pagination = pages[2].select_one(".pagination")

    assert page1_pagination.get_text(" ", strip=True) == "1/4 次へ »"
    assert [element.name for element in page1_pagination.children if element.name] == [
        "span",
        "span",
        "a",
    ]
    assert page1_pagination.select(".empty") == [page1_pagination.find("span")]
    assert (
        page1_pagination.select_one("a[href='/dates/2026-07-12/page/2/']") is not None
    )
    assert "前へ" not in page1_pagination.get_text(" ", strip=True)

    assert page2_pagination.get_text(" ", strip=True) == "« 前へ 2/4 次へ »"
    assert page2_pagination.select_one("a[href='/dates/2026-07-12.html']") is not None
    assert (
        page2_pagination.select_one("a[href='/dates/2026-07-12/page/3/']") is not None
    )

    assert page4_pagination.get_text(" ", strip=True) == "« 前へ 4/4"
    assert [element.name for element in page4_pagination.children if element.name] == [
        "a",
        "span",
        "span",
    ]
    assert page4_pagination.select_one(":scope > span:last-child.empty") is not None
    assert (
        page4_pagination.select_one("a[href='/dates/2026-07-12/page/3/']") is not None
    )
    assert "次へ" not in page4_pagination.get_text(" ", strip=True)

    assert pages[0].find("link", rel="canonical")["href"] == "/dates/2026-07-12.html"
    assert pages[1].find("link", rel="canonical")["href"] == "/dates/2026-07-12/page/2/"
    assert pages[2].find("link", rel="canonical")["href"] == "/dates/2026-07-12/page/4/"

    for parsed in pages:
        day_nav = parsed.select_one(".navigation-day")
        assert day_nav.select_one("a[href='/dates/2026-07-13.html']") is not None
        assert day_nav.select_one("a[href='/dates/2026-07-11.html']") is not None


def test_topic_detail_pagination(generated_site):
    """
    トピックページのページネーションが正しい。
    1ページ目、2ページ目以降、前へ・次へリンク、最終ページの次へリンクなしを確認する。
    """
    out = generated_site.output_dir / "topics" / "shopping"
    page1 = soup(out / "index.html")
    page2 = soup(out / "page" / "2" / "index.html")

    assert (out / "index.html").exists()
    assert (out / "page" / "2" / "index.html").exists()
    assert (
        page1.select_one(".pagination a[href='/topics/shopping/page/2/']") is not None
    )
    assert page1.select_one(".pagination a[href='/topics/shopping/']") is None
    assert page2.select_one(".pagination a[href='/topics/shopping/']") is not None
    assert page2.select_one(".pagination a[href='/topics/shopping/page/3/']") is None


@pytest.mark.parametrize(
    ("first", "second", "last", "second_prev", "second_next"),
    [
        ("index.html", "index_2.html", "index_4.html", "index.html", "index_3.html"),
        (
            "topics.html",
            "topics_2.html",
            "topics_4.html",
            "topics.html",
            "topics_3.html",
        ),
        ("dates.html", "dates_2.html", "dates_3.html", "dates.html", "dates_3.html"),
    ],
)
def test_top_topics_and_dates_pagination(
    generated_site, first, second, last, second_prev, second_next
):
    """
    トップページ・topics.html・dates.html のページネーションが正しい。
    1ページ目、2ページ目、最終ページの前後リンクを確認する。
    """
    out = generated_site.output_dir

    assert soup(out / first).select_one(f".pagination a[href='{second}']") is not None
    assert (
        soup(out / second).select_one(f".pagination a[href='{second_prev}']")
        is not None
    )
    assert (
        soup(out / second).select_one(f".pagination a[href='{second_next}']")
        is not None
    )
    last_pagination = soup(out / last).select_one(".pagination")
    assert last_pagination is not None
    assert "次へ" not in last_pagination.get_text(" ", strip=True)


def test_search_data_urls_exist_and_titles_match_target_html(generated_site):
    """
    search_data.json とHTMLのURL・タイトル整合を確認する。
    検索結果URLから実在HTMLに到達でき、検索タイトルがリンク先HTMLにも表示されることを確認する。
    """
    out = generated_site.output_dir
    search_items = json.loads(
        (out / "json" / "search_data.json").read_text(encoding="utf-8")
    )

    assert search_items
    for item in search_items:
        target = resolve_internal_href(out, out / "search.html", item["url"])
        assert target.exists()
        assert item["title"] in text(target)


def test_css_and_js_references_exist(generated_site):
    """
    CSS/JS参照が存在し、参照先ファイルが存在する。
    stylesheet link と script src の内部参照先を確認する。
    """
    missing = []
    for path in all_html(generated_site.output_dir):
        parsed = soup(path)
        refs = [
            *(link.get("href") for link in parsed.find_all("link", rel="stylesheet")),
            *(script.get("src") for script in parsed.find_all("script", src=True)),
        ]
        for ref in refs:
            if not ref or is_external_or_fragment(ref):
                continue
            target = resolve_internal_href(generated_site.output_dir, path, ref)
            if not target.exists():
                missing.append((path.relative_to(generated_site.output_dir), ref))

    assert missing == []


def test_legacy_topic_redirect_exists_and_new_links_use_slug_urls(generated_site):
    """
    旧トピックURLのリダイレクトと新規リンクのslug URL化を確認する。
    旧URLの誘導先、通常の内部リンクが旧 topics/トピック名.html 形式ではなく slug URL であることを確認する。
    """
    out = generated_site.output_dir
    redirect_path = out / "topics" / "旧トピック名.html"
    parsed_redirect = soup(redirect_path)

    assert redirect_path.exists()
    assert (
        parsed_redirect.find("link", rel="canonical")["href"]
        == "/topics/renamed-topic/"
    )
    assert (
        "/topics/renamed-topic/"
        in parsed_redirect.find("meta", attrs={"http-equiv": "refresh"})["content"]
    )

    old_topic_link_pattern = re.compile(r"/topics/[^/]+\.html$")
    for path in all_html(out):
        for anchor in soup(path).find_all("a", href=True):
            href = anchor["href"]
            assert not old_topic_link_pattern.search(href)

    assert (
        soup(out / "dates" / "2026-01-15.html").find("a", href="/topics/renamed-topic/")
        is not None
    )
