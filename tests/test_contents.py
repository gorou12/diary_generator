import logging
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
    """
    heading_3 からトピックが作られる
    """

    topics, has_pending = fetch_topics(
        monkeypatch,
        [
            block(
                "heading_3", "買い物", block_id="topic-shopping", last_edited_time=OLD
            ),
            block("paragraph", "スーパーで野菜を買った", last_edited_time=OLD),
            block("heading_3", "散歩", block_id="topic-walking", last_edited_time=OLD),
            block("paragraph", "公園で散歩した", last_edited_time=OLD),
        ],
    )

    assert has_pending is False
    assert [topic["title"] for topic in topics] == ["買い物", "散歩"]
    assert topics[0]["topic_id"] == "topic-shopping"
    assert topics[0]["plain_text"] == "スーパーで野菜を買った"


def test_empty_paragraph_in_middle_of_topic_is_kept(monkeypatch):
    """
    トピック途中の空段落は空段落として残す
    """
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
        "<p>公園へ向かった</p>",
        "<br>",
        "<p>公園まで歩いた</p>",
    ]
    assert topics[0]["plain_text"] == "公園へ向かった 公園まで歩いた"


def test_trailing_empty_paragraph_is_not_included_in_body(monkeypatch):
    """
    トピック末尾の空段落は本文に含めない
    """
    topics, _ = fetch_topics(
        monkeypatch,
        [
            block("heading_3", "散歩", last_edited_time=OLD),
            block("paragraph", "公園まで歩いた", last_edited_time=OLD),
            block("paragraph", "", last_edited_time=OLD),
        ],
    )

    assert contents._build_topic_content(topics[0]) == ["<p>公園まで歩いた</p>"]
    assert topics[0]["plain_text"] == "公園まで歩いた"


def test_hash_prefixed_paragraph_is_tag_not_body(monkeypatch):
    """
    # で始まる段落はタグとして扱われ、本文には入らない
    """
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
    """
    非公開トピックは出力しない
    """
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
    """
    編集後5分未満のトピックは出力されず has_pending_topics が True になる
    """
    original_pending_time = config.TOPIC_PENDING_TIME
    object.__setattr__(config, "TOPIC_PENDING_TIME", 5 * 60)
    try:
        topics, has_pending = fetch_topics(
            monkeypatch,
            [
                block(
                    "heading_3", "編集中", last_edited_time=NOW - timedelta(minutes=4)
                ),
                block(
                    "paragraph",
                    "まだ編集中の本文",
                    last_edited_time=NOW - timedelta(minutes=4),
                ),
            ],
        )
    finally:
        object.__setattr__(config, "TOPIC_PENDING_TIME", original_pending_time)

    assert topics == []
    assert has_pending is True


def test_render_supported_blocks(monkeypatch):
    calls = []
    monkeypatch.setattr(
        contents,
        "generate_image_tag",
        lambda block_id, image_url: calls.append((block_id, image_url)) or "<img>",
    )

    blocks = [
        {"type": "paragraph", "plain_text": "通常の文章"},
        {"type": "paragraph"},
        {"type": "bulleted_list_item", "plain_text": "項目1"},
        {"type": "bulleted_list_item", "plain_text": "項目2"},
        {"type": "numbered_list_item", "plain_text": "手順1"},
        {"type": "numbered_list_item", "plain_text": "手順2"},
        {"type": "bulleted_list_item", "plain_text": "別項目"},
        {"type": "to_do", "plain_text": "完了した項目", "checked": True},
        {"type": "to_do", "plain_text": "未完了", "checked": False},
        {"type": "quote", "plain_text": "引用文"},
        {"type": "divider"},
        {"type": "heading_4", "plain_text": "小見出し"},
        {
            "type": "callout",
            "plain_text": "注意",
            "icon": {"type": "emoji", "emoji": "💡"},
        },
        {
            "type": "image",
            "block_id": "image-1",
            "image": {"url": "https://example.com/image.png"},
        },
        {"type": "unsupported", "plain_text": "フォールバック"},
        {"type": "unsupported"},
    ]

    assert contents.render_blocks(blocks) == [
        "<p>通常の文章</p>",
        "<br>",
        "<ul><li>項目1</li><li>項目2</li></ul>",
        "<ol><li>手順1</li><li>手順2</li></ol>",
        "<ul><li>別項目</li></ul>",
        '<label class="todo"><input type="checkbox" disabled checked><span>完了した項目</span></label>',
        '<label class="todo"><input type="checkbox" disabled><span>未完了</span></label>',
        "<blockquote>引用文</blockquote>",
        "<hr>",
        "<h4>小見出し</h4>",
        '<div class="callout"><span class="callout-icon">💡</span><div>注意</div></div>',
        "<img>",
        "<p>フォールバック</p>",
    ]
    assert calls == [("image-1", "https://example.com/image.png")]


def test_render_rich_text_and_escape_html():
    rendered = contents.render_block(
        {
            "type": "paragraph",
            "rich_text": [
                {
                    "text": "link & bold",
                    "href": 'https://example.com/?q=<x>&a="b"',
                    "annotations": {"bold": True},
                },
                {"text": " italic", "annotations": {"italic": True}},
                {"text": " strike", "annotations": {"strikethrough": True}},
                {"text": " underline", "annotations": {"underline": True}},
                {"text": " code <tag>", "annotations": {"code": True}},
            ],
        }
    )

    assert rendered == (
        '<p><a href="https://example.com/?q=&lt;x&gt;&amp;a=&quot;b&quot;" '
        'target="_blank" rel="noopener noreferrer"><strong>link &amp; bold</strong></a>'
        "<em> italic</em><s> strike</s><u> underline</u><code> code &lt;tag&gt;</code></p>"
    )


def test_render_rich_text_validates_link_schemes_and_escapes_values():
    rich_text = [
        {"text": "https", "href": "https://example.com/?q=<x>", "annotations": {}},
        {"text": " http", "href": "http://example.com", "annotations": {}},
        {"text": " mail", "href": "mailto:test@example.com", "annotations": {}},
        {"text": " js", "href": "javascript:alert(1)", "annotations": {}},
        {"text": " data <tag>", "href": "data:text/html,<p>x</p>", "annotations": {}},
    ]

    rendered = contents.render_block({"type": "paragraph", "rich_text": rich_text})

    assert rendered == (
        '<p><a href="https://example.com/?q=&lt;x&gt;" target="_blank" '
        'rel="noopener noreferrer">https</a>'
        '<a href="http://example.com" target="_blank" rel="noopener noreferrer"> http</a>'
        '<a href="mailto:test@example.com" target="_blank" rel="noopener noreferrer"> mail</a>'
        " js data &lt;tag&gt;</p>"
    )


def test_standalone_url_rich_text_paragraph_is_not_prelinked():
    rendered = contents.render_block(
        {
            "type": "paragraph",
            "rich_text": [
                {
                    "text": "https://example.com/page",
                    "href": "https://example.com/page",
                    "annotations": {},
                }
            ],
        }
    )

    assert rendered == "<p>https://example.com/page</p>"


def test_standalone_url_rich_text_paragraph_becomes_link_card(monkeypatch):
    monkeypatch.setattr(contents.linkcard.linkcard, "ogp_cache", {})
    monkeypatch.setattr(
        contents.linkcard,
        "fetch_data",
        lambda url: {"title": "Example", "description": "Description", "image": ""},
    )
    rendered = contents.render_block(
        {
            "type": "paragraph",
            "rich_text": [
                {
                    "text": "https://example.com/page",
                    "href": "https://example.com/page",
                    "annotations": {},
                }
            ],
        }
    )

    linked = contents.linkcard.create([rendered])[0]

    assert '<div class="link-card">' in linked
    assert '<a href="https://example.com/page" target="_blank">' in linked


def test_named_link_rich_text_paragraph_stays_inline_anchor():
    rendered = contents.render_block(
        {
            "type": "paragraph",
            "rich_text": [
                {
                    "text": "こちら",
                    "href": "https://example.com",
                    "annotations": {},
                }
            ],
        }
    )

    assert rendered == (
        '<p><a href="https://example.com" target="_blank" '
        'rel="noopener noreferrer">こちら</a></p>'
    )


def test_url_link_inside_sentence_stays_inline_anchor():
    rendered = contents.render_block(
        {
            "type": "paragraph",
            "rich_text": [
                {"text": "see ", "annotations": {}},
                {
                    "text": "https://example.com",
                    "href": "https://example.com",
                    "annotations": {},
                },
            ],
        }
    )

    assert rendered == (
        '<p>see <a href="https://example.com" target="_blank" '
        'rel="noopener noreferrer">https://example.com</a></p>'
    )


def test_standalone_disallowed_scheme_url_is_not_linked_or_carded(monkeypatch):
    monkeypatch.setattr(contents.linkcard, "fetch_data", lambda url: None)
    rendered = contents.render_block(
        {
            "type": "paragraph",
            "rich_text": [
                {
                    "text": "javascript:alert(1)",
                    "href": "javascript:alert(1)",
                    "annotations": {},
                }
            ],
        }
    )

    assert rendered == "<p>javascript:alert(1)</p>"
    assert contents.linkcard.create([rendered]) == [rendered]


def test_normalize_block_preserves_type_specific_display_data():
    todo = {
        "id": "todo-1",
        "type": "to_do",
        "to_do": {"rich_text": [], "checked": True},
    }
    callout = {
        "id": "callout-1",
        "type": "callout",
        "callout": {"rich_text": [], "icon": {"type": "emoji", "emoji": "📌"}},
    }
    image = {
        "id": "image-1",
        "type": "image",
        "image": {
            "type": "external",
            "external": {"url": "https://example.com/a.png"},
        },
    }

    assert contents._normalize_block(todo)["checked"] is True
    assert contents._normalize_block(callout)["icon"] == {
        "type": "emoji",
        "emoji": "📌",
    }
    normalized_image = contents._strip_block_runtime_fields(
        contents._normalize_block(image)
    )
    assert normalized_image == {
        "block_id": "image-1",
        "type": "image",
        "image": {"url": "https://example.com/a.png", "source_type": "external"},
    }


def test_cache_schema_version_changed_for_old_cache_regeneration():
    assert contents.CACHE_SCHEMA_VERSION == 4


def test_linkcard_keeps_rich_text_anchor_intact(monkeypatch):
    monkeypatch.setattr(contents.linkcard, "fetch_data", lambda url: None)
    content = [
        contents.render_block(
            {
                "type": "paragraph",
                "rich_text": [
                    {
                        "text": "Example",
                        "href": "https://example.com",
                        "annotations": {},
                    }
                ],
            }
        )
    ]

    assert contents.linkcard.create(content) == content


def test_linkcard_keeps_anchor_with_url_text_intact(monkeypatch):
    monkeypatch.setattr(contents.linkcard, "fetch_data", lambda url: None)
    content = ['<a href="https://example.com">https://example.com</a>']

    assert contents.linkcard.create(content) == content


def test_linkcard_keeps_anchor_with_link_label_intact(monkeypatch):
    monkeypatch.setattr(contents.linkcard, "fetch_data", lambda url: None)
    content = ['<a href="https://example.com">リンク名</a>']

    assert contents.linkcard.create(content) == content


def test_linkcard_does_not_convert_image_src_url(monkeypatch):
    monkeypatch.setattr(contents.linkcard, "fetch_data", lambda url: None)
    content = ['<img class="callout-icon" alt="" src="https://example.com/icon.png">']

    assert contents.linkcard.create(content) == content


def test_linkcard_converts_standalone_url_outside_html_tags(monkeypatch):
    monkeypatch.setattr(contents.linkcard, "fetch_data", lambda url: None)

    assert contents.linkcard.create(["https://example.com/page"]) == [
        '<a href="https://example.com/page" target="_blank">https://example.com/page</a>'
    ]


def test_linkcard_handles_mixed_html_tag_and_plain_urls(monkeypatch):
    monkeypatch.setattr(contents.linkcard, "fetch_data", lambda url: None)
    content = [
        '<img class="callout-icon" alt="" src="https://example.com/icon.png"> '
        "https://example.com/page"
    ]

    assert contents.linkcard.create(content) == [
        '<img class="callout-icon" alt="" src="https://example.com/icon.png"> '
        '<a href="https://example.com/page" target="_blank">https://example.com/page</a>'
    ]


def test_render_callout_icon_falls_back_for_unknown_icon_format():
    assert (
        contents.render_block(
            {
                "type": "callout",
                "plain_text": "本文のみ",
                "icon": {"type": "custom", "value": {"unexpected": True}},
            }
        )
        == '<div class="callout"><div>本文のみ</div></div>'
    )


def test_render_callout_icon_validates_image_url_scheme():
    assert contents.render_block(
        {
            "type": "callout",
            "plain_text": "本文",
            "icon": {"type": "external", "url": "https://example.com/icon.png"},
        }
    ) == (
        '<div class="callout"><img class="callout-icon" alt="" '
        'src="https://example.com/icon.png"><div>本文</div></div>'
    )
    assert (
        contents.render_block(
            {
                "type": "callout",
                "plain_text": "本文",
                "icon": {"type": "external", "url": "javascript:alert(1)"},
            }
        )
        == '<div class="callout"><div>本文</div></div>'
    )


def test_fetch_page_recursively_normalizes_child_blocks(monkeypatch):
    calls = []
    parent = block(
        "bulleted_list_item",
        "1段目",
        block_id="parent",
        last_edited_time=OLD,
    )
    parent["has_children"] = True
    child = block(
        "bulleted_list_item",
        "2段目",
        block_id="child",
        last_edited_time=OLD,
    )

    def fake_get_block_children(block_id, start_cursor=None):
        calls.append((block_id, start_cursor))
        if block_id == "page-1":
            return notion_children_response(
                [block("heading_3", "リスト", last_edited_time=OLD), parent]
            )
        if block_id == "parent":
            return notion_children_response([child])
        return notion_children_response([])

    monkeypatch.setattr(notion_api, "get_block_children", fake_get_block_children)

    topics, has_pending = contents._fetch_diary_page("page-1", NOW)

    assert has_pending is False
    assert calls == [("page-1", None), ("parent", None)]
    assert topics[0]["blocks"][0]["children"][0]["plain_text"] == "2段目"
    assert topics[0]["plain_text"] == "1段目 2段目"


def test_fetch_children_paginates_child_blocks(monkeypatch):
    parent = block(
        "bulleted_list_item", "1段目", block_id="parent", last_edited_time=OLD
    )
    parent["has_children"] = True
    child_1 = block(
        "bulleted_list_item", "2段目-1", block_id="child-1", last_edited_time=OLD
    )
    child_2 = block(
        "bulleted_list_item", "2段目-2", block_id="child-2", last_edited_time=OLD
    )

    def fake_get_block_children(block_id, start_cursor=None):
        if block_id == "page-1":
            return notion_children_response(
                [block("heading_3", "リスト", last_edited_time=OLD), parent]
            )
        if block_id == "parent" and start_cursor is None:
            return {"results": [child_1], "has_more": True, "next_cursor": "next"}
        if block_id == "parent" and start_cursor == "next":
            return notion_children_response([child_2])
        return notion_children_response([])

    monkeypatch.setattr(notion_api, "get_block_children", fake_get_block_children)

    topics, _ = contents._fetch_diary_page("page-1", NOW)

    assert [child["plain_text"] for child in topics[0]["blocks"][0]["children"]] == [
        "2段目-1",
        "2段目-2",
    ]


def test_fetch_page_skips_child_api_when_has_children_is_false(monkeypatch):
    calls = []
    item = block("bulleted_list_item", "1段目", block_id="item", last_edited_time=OLD)
    item["has_children"] = False

    def fake_get_block_children(block_id, start_cursor=None):
        calls.append((block_id, start_cursor))
        return notion_children_response(
            [block("heading_3", "リスト", last_edited_time=OLD), item]
        )

    monkeypatch.setattr(notion_api, "get_block_children", fake_get_block_children)

    contents._fetch_diary_page("page-1", NOW)

    assert calls == [("page-1", None)]


def test_child_last_edited_time_controls_pending(monkeypatch):
    original_pending_time = config.TOPIC_PENDING_TIME
    parent = block(
        "bulleted_list_item", "1段目", block_id="parent", last_edited_time=OLD
    )
    parent["has_children"] = True
    child = block(
        "bulleted_list_item",
        "編集中",
        block_id="child",
        last_edited_time=NOW - timedelta(minutes=4),
    )

    def fake_get_block_children(block_id, start_cursor=None):
        if block_id == "page-1":
            return notion_children_response(
                [block("heading_3", "リスト", last_edited_time=OLD), parent]
            )
        if block_id == "parent":
            return notion_children_response([child])
        return notion_children_response([])

    object.__setattr__(config, "TOPIC_PENDING_TIME", 5 * 60)
    try:
        monkeypatch.setattr(notion_api, "get_block_children", fake_get_block_children)
        topics, has_pending = contents._fetch_diary_page("page-1", NOW)
    finally:
        object.__setattr__(config, "TOPIC_PENDING_TIME", original_pending_time)

    assert topics == []
    assert has_pending is True


def test_render_nested_list_structures():
    assert contents.render_blocks(
        [
            {
                "type": "bulleted_list_item",
                "plain_text": "1段目",
                "children": [
                    {"type": "numbered_list_item", "plain_text": "2段目-1"},
                    {"type": "numbered_list_item", "plain_text": "2段目-2"},
                    {"type": "bulleted_list_item", "plain_text": "2段目-3"},
                ],
            }
        ]
    ) == [
        "<ul><li>1段目<ol><li>2段目-1</li><li>2段目-2</li></ol>"
        "<ul><li>2段目-3</li></ul></li></ul>"
    ]


def test_render_numbered_parent_with_bulleted_grandchild_and_non_list_children():
    assert contents.render_blocks(
        [
            {
                "type": "numbered_list_item",
                "plain_text": "1段目",
                "children": [
                    {
                        "type": "bulleted_list_item",
                        "plain_text": "2段目",
                        "children": [
                            {"type": "bulleted_list_item", "plain_text": "3段目"},
                        ],
                    }
                ],
            }
        ]
    ) == ["<ol><li>1段目<ul><li>2段目<ul><li>3段目</li></ul></li></ul></li></ol>"]


def test_list_item_paragraph_child_is_hidden_and_warns(caplog):
    caplog.set_level(logging.WARNING, logger="diary_system")

    assert contents.render_blocks(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "plain_text": "1段目",
                "children": [
                    {
                        "block_id": "paragraph-1",
                        "type": "paragraph",
                        "plain_text": "補足",
                    },
                ],
            }
        ]
    ) == ["<ul><li>1段目</li></ul>"]

    assert caplog.text == ""


def test_list_item_to_do_child_is_hidden_and_warns(caplog):
    caplog.set_level(logging.WARNING, logger="diary_system")

    assert contents.render_blocks(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "plain_text": "1段目",
                "children": [
                    {
                        "block_id": "todo-1",
                        "type": "to_do",
                        "plain_text": "確認",
                        "checked": False,
                    },
                ],
            }
        ]
    ) == ["<ul><li>1段目</li></ul>"]

    assert caplog.text == ""


def test_unknown_child_block_does_not_break_rendering(monkeypatch, caplog):
    parent = block(
        "bulleted_list_item", "1段目", block_id="parent", last_edited_time=OLD
    )
    parent["has_children"] = True
    unknown = block("unsupported", "未対応", block_id="unknown", last_edited_time=OLD)

    def fake_get_block_children(block_id, start_cursor=None):
        if block_id == "page-1":
            return notion_children_response(
                [block("heading_3", "リスト", last_edited_time=OLD), parent]
            )
        if block_id == "parent":
            return notion_children_response([unknown])
        return notion_children_response([])

    monkeypatch.setattr(notion_api, "get_block_children", fake_get_block_children)
    caplog.set_level(logging.WARNING, logger="diary_system")

    topics, _ = contents._fetch_diary_page("page-1", NOW)

    assert contents._build_topic_content(topics[0]) == ["<ul><li>1段目</li></ul>"]
    assert caplog.text == ""


def test_non_list_block_children_emit_warning_without_rendering(caplog):
    caplog.set_level(logging.WARNING, logger="diary_system")

    assert contents.render_blocks(
        [
            {
                "block_id": "paragraph-1",
                "type": "paragraph",
                "plain_text": "親段落",
                "children": [
                    {"type": "paragraph", "plain_text": "非表示の子"},
                ],
            }
        ]
    ) == ["<p>親段落</p>"]

    assert caplog.text == ""


def _detail_entries_with_blocks(
    blocks, *, page_id="page-1", topic_id="topic-1", title="今日の記録"
):
    return [
        {
            "page_id": page_id,
            "page_name": "20260717",
            "entry_date": "2026-07-17",
            "topics": [
                {
                    "topic_id": topic_id,
                    "title": title,
                    "blocks": blocks,
                }
            ],
        }
    ]


def _collect_warnings(blocks):
    return contents._collect_unsupported_nested_block_warnings(
        _detail_entries_with_blocks(blocks)
    )


def test_unsupported_nested_warning_contains_entry_topic_and_block_context(caplog):
    warnings = _collect_warnings(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "plain_text": "1段目",
                "children": [
                    {
                        "block_id": "paragraph-1",
                        "type": "paragraph",
                        "plain_text": "補足",
                    },
                ],
            }
        ]
    )

    assert len(warnings) == 1
    warning = warnings[0]
    assert warning["entry_date"] == "2026-07-17"
    assert warning["topic_title"] == "今日の記録"
    assert warning["topic_id"] == "topic-1"
    assert warning["parent_block_id"] == "list-1"
    assert warning["parent_type"] == "bulleted_list_item"
    assert warning["child_block_id"] == "paragraph-1"
    assert warning["child_type"] == "paragraph"

    caplog.set_level(logging.WARNING, logger="diary_system")
    contents._log_new_unsupported_nested_block_warnings(warnings, [])
    assert "entry_date=2026-07-17" in caplog.text
    assert "topic_title=今日の記録" in caplog.text
    assert "topic_id=topic-1" in caplog.text
    assert "parent_block_id=list-1" in caplog.text
    assert "parent_type=bulleted_list_item" in caplog.text
    assert "child_block_id=paragraph-1" in caplog.text
    assert "child_type=paragraph" in caplog.text


def test_first_detection_logs_warning_and_same_warning_next_time_is_suppressed(caplog):
    warnings = _collect_warnings(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "children": [{"block_id": "paragraph-1", "type": "paragraph"}],
            }
        ]
    )
    caplog.set_level(logging.WARNING, logger="diary_system")
    contents._log_new_unsupported_nested_block_warnings(warnings, [])
    assert "child_block_id=paragraph-1" in caplog.text

    caplog.clear()
    contents._log_new_unsupported_nested_block_warnings(warnings, warnings)
    assert caplog.text == ""


def test_added_unsupported_child_logs_only_added_warning(caplog):
    previous = _collect_warnings(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "children": [{"block_id": "paragraph-1", "type": "paragraph"}],
            }
        ]
    )
    current = _collect_warnings(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "children": [
                    {"block_id": "paragraph-1", "type": "paragraph"},
                    {"block_id": "todo-1", "type": "to_do"},
                ],
            }
        ]
    )
    caplog.set_level(logging.WARNING, logger="diary_system")
    contents._log_new_unsupported_nested_block_warnings(current, previous)
    assert "child_block_id=todo-1" in caplog.text
    assert "child_block_id=paragraph-1" not in caplog.text


def test_block_type_change_is_new_warning(caplog):
    previous = _collect_warnings(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "children": [{"block_id": "child-1", "type": "paragraph"}],
            }
        ]
    )
    current = _collect_warnings(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "children": [{"block_id": "child-1", "type": "to_do"}],
            }
        ]
    )
    caplog.set_level(logging.WARNING, logger="diary_system")
    contents._log_new_unsupported_nested_block_warnings(current, previous)
    assert "child_block_id=child-1" in caplog.text
    assert "child_type=to_do" in caplog.text


def test_resolved_warning_is_removed_from_current_cache_and_reappears_as_new(caplog):
    previous = _collect_warnings(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "children": [{"block_id": "child-1", "type": "paragraph"}],
            }
        ]
    )
    resolved = _collect_warnings(
        [
            {
                "block_id": "list-1",
                "type": "bulleted_list_item",
                "children": [{"block_id": "child-list", "type": "bulleted_list_item"}],
            }
        ]
    )
    assert resolved == []

    reappeared = previous
    caplog.set_level(logging.WARNING, logger="diary_system")
    contents._log_new_unsupported_nested_block_warnings(reappeared, resolved)
    assert "child_block_id=child-1" in caplog.text


def test_non_list_block_children_warning_has_child_count_and_html_still_renders():
    blocks = [
        {
            "block_id": "paragraph-1",
            "type": "paragraph",
            "plain_text": "親段落",
            "children": [{"block_id": "paragraph-2", "type": "paragraph"}],
        }
    ]
    warnings = _collect_warnings(blocks)
    assert warnings[0]["unsupported_block_id"] == "paragraph-1"
    assert warnings[0]["unsupported_block_type"] == "paragraph"
    assert warnings[0]["unsupported_block_child_count"] == 1
    assert contents.render_blocks(blocks) == ["<p>親段落</p>"]


def test_nested_normal_bulleted_and_numbered_lists_do_not_warn():
    assert (
        _collect_warnings(
            [
                {
                    "block_id": "list-1",
                    "type": "bulleted_list_item",
                    "children": [
                        {"block_id": "list-2", "type": "numbered_list_item"},
                        {"block_id": "list-3", "type": "bulleted_list_item"},
                    ],
                }
            ]
        )
        == []
    )
