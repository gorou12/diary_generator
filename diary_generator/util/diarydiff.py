from typing import Any

from diary_generator.logger import notifylogger

notify_log = notifylogger.get_logger()


def diff_detail_entries(
    old_entries: list[dict[str, Any]],
    new_entries: list[dict[str, Any]],
) -> None:
    """diary_detail.json の entries 同士を比較し、差分を Discord 通知ログに出力する。

    比較単位はトピック（topic_id を主キー）。
    判定: 新規 / 削除 / 更新（last_edited_time の変化）。
    """
    if not old_entries and new_entries:
        notify_log.info("Diaryを新しくダウンロードしました")
        return

    if not old_entries or not new_entries:
        notify_log.warning("差分を取ろうとしましたが、どちらかのデータが空みたいです")
        return

    old_topics = _index_topics_by_id(old_entries)
    new_topics = _index_topics_by_id(new_entries)

    results: list[str] = []

    for topic_id, (date, title, _) in old_topics.items():
        if topic_id not in new_topics:
            results.append(f"del: {date} → {title}")

    for topic_id, (date, title, last_edited) in new_topics.items():
        if topic_id not in old_topics:
            results.append(f"add: {date} → {title}")
            continue
        old_last_edited = old_topics[topic_id][2]
        if last_edited != old_last_edited:
            results.append(f"changed: {date} → {title}")

    if results:
        notify_log.info("\n" + "\n".join(results))


def _index_topics_by_id(
    entries: list[dict[str, Any]],
) -> dict[str, tuple[str, str, str]]:
    """entries から topic_id をキーに {topic_id: (date, title, last_edited_time)} を返す。"""
    index: dict[str, tuple[str, str, str]] = {}
    for entry in entries:
        date = entry.get("entry_date", "")
        for topic in entry.get("topics", []):
            topic_id = topic.get("topic_id", "")
            if not topic_id:
                continue
            title = topic.get("title", "")
            last_edited = topic.get("last_edited_time", "")
            index[topic_id] = (date, title, last_edited)
    return index
