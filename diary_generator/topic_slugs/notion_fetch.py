"""トピックスラッグ用 Notion データベースからページ一覧を取得する。"""

from diary_generator import notion_api


def _format_database_id(database_id: str) -> str:
    """ハイフンなし 32 桁の ID を Notion API 向け UUID 形式にそろえる。"""
    s = database_id.strip().replace("-", "")
    if len(s) == 32:
        return f"{s[:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:]}"
    return database_id.strip()


def fetch_all_slug_database_pages(database_id: str) -> list[dict]:
    """`query_database` をページネーションで繰り返し、ページオブジェクトのリストを返す。"""
    db_id = _format_database_id(database_id)
    all_pages: list[dict] = []
    cursor: str | None = None
    while True:
        data = notion_api.query_database(db_id, start_cursor=cursor)
        all_pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return all_pages
