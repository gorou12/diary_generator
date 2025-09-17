from .client import notion_request


def get_block_children(block_id: str, start_cursor: str = None) -> dict:
    endpoint = f"blocks/{block_id}/children"
    params = {}
    if start_cursor:
        params["start_cursor"] = start_cursor
    params["page_size"] = 100

    return notion_request("GET", endpoint, params=params)
