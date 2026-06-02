from datetime import datetime, timezone
from typing import Any


def rich_text(text: str) -> list[dict[str, Any]]:
    return [
        {
            "type": "text",
            "plain_text": text,
            "text": {"content": text},
            "href": None,
            "annotations": {},
        }
    ]


def block(
    block_type: str,
    text: str = "",
    *,
    block_id: str | None = None,
    last_edited_time: datetime | str | None = None,
) -> dict[str, Any]:
    if last_edited_time is None:
        last_edited_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    if isinstance(last_edited_time, datetime):
        last_edited_time = last_edited_time.isoformat()

    return {
        "id": block_id or f"{block_type}-{abs(hash((block_type, text))) & 0xffff:x}",
        "type": block_type,
        "last_edited_time": last_edited_time,
        block_type: {"rich_text": rich_text(text)},
    }


def notion_children_response(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    return {"results": blocks, "has_more": False, "next_cursor": None}
