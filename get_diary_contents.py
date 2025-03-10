import configparser
import json
import os
import re

import requests
from dotenv import load_dotenv

# Notion API 設定
# .env ファイルを読み込む
load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

config = configparser.ConfigParser()
config.read("config/settings.ini")

CACHE_FILE = config.get("settings", "CacheFileName")

if not CACHE_FILE:
    raise Exception("settings.iniから値を読めませんでした")


def fetch_notion_data(use_cache=False):
    """Notion API からデータを取得する（キャッシュ対応）"""
    if use_cache and os.path.exists(CACHE_FILE):
        print("✅ キャッシュからデータを読み込みます")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    print("🔄 Notion API からデータを取得中...")
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)

    if response.status_code == 200:
        print("✅ Notion DBデータ取得完了")
        data = response.json()

        all_pages = []
        for item in data.get("results", []):
            properties = item.get("properties", {})
            date = properties.get("日付", {}).get("date", {}).get("start", "")
            page_id = item.get("id", "")
            is_public = properties.get("公開", {}).get("checkbox", False)

            if not date or not is_public:
                continue  # 非公開ページはスキップ

            topics = fetch_page_content(page_id)
            print(f"- 日付データ({date}) 取得完了")
            all_pages.append({"date": date, "topics": topics})

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(all_pages, f, ensure_ascii=False, indent=4)
        print("✅ Notionデータ取得＆キャッシュ完了")
        return all_pages
    else:
        print(f"⚠️ APIエラー: {response.status_code}")
        print(response.text)
        return None


def fetch_page_content(page_id):
    """特定のページの詳細を取得し、本文を解析して返す"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        blocks = response.json().get("results", [])
        topics = []
        current_topic = {"title": "", "content": [], "hashtags": []}

        for block in blocks:
            block_type = block.get("type")
            text_elements = (
                block[block_type].get("rich_text", []) if block_type in block else []
            )
            text_content = "".join(
                t["text"]["content"] for t in text_elements if "text" in t
            ).strip()

            if block_type == "heading_3":  # Notionの「見出し3」がトピック名に相当
                if current_topic["title"] and "非公開" not in current_topic["hashtags"]:
                    topics.append(current_topic)  # 既存のトピックを保存

                current_topic = {"title": text_content, "content": [], "hashtags": []}
            elif text_content.startswith("#"):
                hashtags = re.findall(r"#(\S+)", text_content)
                current_topic["hashtags"].extend(hashtags)
            elif text_content:
                current_topic["content"].append(text_content.replace("\n", "<br>"))

        if current_topic["title"] and "非公開" not in current_topic["hashtags"]:
            topics.append(current_topic)

        return topics
    else:
        print(f"⚠️ ページコンテンツ取得エラー: {response.status_code}")
        return []


def load_notion_data():
    """保存された Notion データを読み込む"""
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)
