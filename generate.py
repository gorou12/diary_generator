import requests
import json
import os
from dotenv import load_dotenv

# .env ファイルを読み込む
load_dotenv()

# Notion API 設定
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def fetch_notion_data():
    """Notion API からデータを取得し、一時保存する"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    
    if response.status_code == 200:
        data = response.json()
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("✅ Notionデータ取得完了")
        return data
    else:
        print(f"⚠️ APIエラー: {response.status_code}")
        print(response.text)
        return None

def load_notion_data():
    """保存された Notion データを読み込む"""
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_top_page(data):
    """トップページを生成する"""
    print("✅ トップページ生成")
    # ここにHTML生成ロジックを追加

def generate_topic_pages(data):
    """トピックページを生成する"""
    print("✅ トピックページ生成")
    # ここにHTML生成ロジックを追加

def generate_date_pages(data):
    """日付ページを生成する"""
    print("✅ 日付ページ生成")
    # ここにHTML生成ロジックを追加

if __name__ == "__main__":
    data = fetch_notion_data()
    if data:
        generate_top_page(data)
        generate_topic_pages(data)
        generate_date_pages(data)
