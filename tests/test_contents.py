from datetime import datetime, timedelta, timezone

from diary_generator import contents, notion_api
from diary_generator.config.configuration import config

from .helpers import block, notion_children_response

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
OLD = NOW - timedelta(minutes=10)


def fetch_topics(monkeypatch, blocks, *, now=NOW):
    monkeypatch.setattr(
        notion_api,
        "get_block_children",
        lambda page_id, start_cursor=None: notion_children_response(blocks),
    )
    topics, has_pending = contents._fetch_diary_page("page-1", now)
    return topics, has_pending


def test_heading_3_creates_topic(monkeypatch):
    topics, has_pending = fetch_topics(
        monkeypatch,
        [
            block("heading_3", "買い物", block_id="topic-shopping", last_edited_time=OLD),
            block("paragraph", "スーパーで野菜を買った", last_edited_time=OLD),
        ],
    )

    assert has_pending is False
    assert [topic["title"] for topic in topics] == ["買い物"]
    assert topics[0]["topic_id"] == "topic-shopping"
    assert topics[0]["plain_text"] == "スーパーで野菜を買った"


def test_empty_paragraph_in_middle_of_topic_is_kept(monkeypatch):
    topics, _ = fetch_topics(
        monkeypatch,
        [
            block("heading_3", "散歩", last_edited_time=OLD),
            block("paragraph", "公園へ向かった", last_edited_time=OLD),
            block("paragraph", "", last_edited_time=OLD),
            block("paragraph", "公園まで歩いた", last_edited_time=OLD),
        ],
    )

    assert contents._build_topic_content(topics[0]) == [
        "公園へ向かった",
        "<br>",
        "公園まで歩いた",
    ]
    assert topics[0]["plain_text"] == "公園へ向かった 公園まで歩いた"


def test_trailing_empty_paragraph_is_not_included_in_body(monkeypatch):
    topics, _ = fetch_topics(
        monkeypatch,
        [
            block("heading_3", "散歩", last_edited_time=OLD),
            block("paragraph", "公園まで歩いた", last_edited_time=OLD),
            block("paragraph", "", last_edited_time=OLD),
        ],
    )

    assert contents._build_topic_content(topics[0]) == ["公園まで歩いた"]
    assert topics[0]["plain_text"] == "公園まで歩いた"


def test_hash_prefixed_paragraph_is_tag_not_body(monkeypatch):
    topics, _ = fetch_topics(
        monkeypatch,
        [
            block("heading_3", "読書", last_edited_time=OLD),
            block("paragraph", "#本 #メモ", last_edited_time=OLD),
            block("paragraph", "小説を読み終えた", last_edited_time=OLD),
        ],
    )

    assert topics[0]["tags"] == ["本", "メモ"]
    assert [body["plain_text"] for body in topics[0]["blocks"]] == ["小説を読み終えた"]
    assert "#本" not in topics[0]["plain_text"]


def test_private_topic_is_not_output(monkeypatch):
    topics, has_pending = fetch_topics(
        monkeypatch,
        [
            block("heading_3", "秘密 #非公開", last_edited_time=OLD),
            block("paragraph", "これは出力しない", last_edited_time=OLD),
            block("heading_3", "公開", last_edited_time=OLD),
            block("paragraph", "これは出力する", last_edited_time=OLD),
        ],
    )

    assert has_pending is False
    assert [topic["title"] for topic in topics] == ["公開"]


def test_topic_edited_less_than_five_minutes_ago_is_pending(monkeypatch):
    original_pending_time = config.TOPIC_PENDING_TIME
    object.__setattr__(config, "TOPIC_PENDING_TIME", 5 * 60)
    try:
        topics, has_pending = fetch_topics(
            monkeypatch,
            [
                block("heading_3", "編集中", last_edited_time=NOW - timedelta(minutes=4)),
                block("paragraph", "まだ編集中の本文", last_edited_time=NOW - timedelta(minutes=4)),
            ],
        )
    finally:
        object.__setattr__(config, "TOPIC_PENDING_TIME", original_pending_time)

    assert topics == []
    assert has_pending is True
