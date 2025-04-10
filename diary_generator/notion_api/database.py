from diary_generator.notion_api.client import notion_request


def query_database(database_id: str, start_cursor: str = None) -> dict:
    payload = {}
    if start_cursor:
        payload["start_cursor"] = start_cursor
    payload["page_size"] = 100

    endpoint = f"databases/{database_id}/query"
    return notion_request("POST", endpoint, json=payload or {})
