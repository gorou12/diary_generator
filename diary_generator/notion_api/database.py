from .client import notion_request


def query_database(database_id: str, query: dict = None) -> dict:
    endpoint = f"databases/{database_id}/query"
    return notion_request("POST", endpoint, json=query or {})
