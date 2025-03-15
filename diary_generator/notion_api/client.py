import requests

from diary_generator.config.configuration import config

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_API_VERSION = "2022-06-28"


def notion_request(method: str, endpoint: str, json=None) -> dict:
    url = f"{NOTION_API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {config.ENV.NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }
    response = requests.request(method, url, headers=headers, json=json)

    if response.status_code != 200:
        raise Exception(f"Notion API Error {response.status_code}: {response.text}")

    return response.json()
