from __future__ import annotations


def topic_anchor_id(topic_id: str) -> str:
    return f"topic-{topic_id}"


def entry_permalink(topic_id: str) -> str:
    return f"/entries/{topic_id}/"


def date_url(date: str, page_num: int = 1) -> str:
    if page_num <= 1:
        return f"/dates/{date}.html"
    return f"/dates/{date}/page/{page_num}/"


def date_topic_url(date: str, topic_id: str, page_num: int = 1) -> str:
    return f"{date_url(date, page_num)}#{topic_anchor_id(topic_id)}"
