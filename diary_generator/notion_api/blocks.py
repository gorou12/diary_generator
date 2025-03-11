from .client import notion_request


def get_block_children(block_id: str) -> dict:
    endpoint = f"blocks/{block_id}/children"
    return notion_request("GET", endpoint)
