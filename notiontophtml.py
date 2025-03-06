import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# === Notion APIの設定 ===
load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")  # Notionのインテグレーションで取得
DATABASE_ID = os.getenv("DATABASE_ID")  # Notionの日記データベースID
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# === 最新の日記データを取得（例: 直近30日分） ===
def fetch_latest_entries(limit=30):
    """直近の日記データをNotion APIから取得"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    today = datetime.today().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.today() - timedelta(days=limit)).strftime("%Y-%m-%d")

    data = {
        "filter": {
            "property": "日付",
            "date": {
                "on_or_after": thirty_days_ago
            }
        },
        "sorts": [
            {"property": "日付", "direction": "descending"}  # 新しい順にソート
        ],
        "page_size": 100  # 最大100件取得
    }

    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code != 200:
        print(f"Error fetching data: {response.json()}")
        return []

    db_data = response.json().get("results", [])
    entries_by_date = {}
    
    for page in db_data:
        date = page["properties"]["日付"]["date"]["start"]  # 日付取得
        page_id = page["id"]
        page_entries = fetch_page_blocks(page_id)  # トピック取得
        
        if date not in entries_by_date:
            entries_by_date[date] = []
        
        for entry in page_entries:
            entry["date"] = date  # 各トピックに日付を付与
            entries_by_date[date].append(entry)
    
    return entries_by_date

# === 各ページのブロックを取得（トピックごとに整理） ===
def fetch_page_blocks(page_id):
    """ページのブロックを取得し、トピックごとに整理"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Error fetching page blocks: {response.json()}")
        return []

    blocks = response.json().get("results", [])
    
    entries = []
    current_topic = None
    current_content = []
    
    for block in blocks:
        if block["type"] == "heading_3":
            if current_topic:
                entries.append({"topic": current_topic, "content": "\n".join(current_content)})
                current_content = []
            current_topic = extract_rich_text(block["heading_3"]["rich_text"])
        
        elif block["type"] == "paragraph":
            if block["paragraph"]["rich_text"]:
                current_content.append(extract_rich_text(block["paragraph"]["rich_text"]))
    
    if current_topic:
        entries.append({"topic": current_topic, "content": "\n".join(current_content)})
    
    return entries

# === リッチテキストを処理 ===
def extract_rich_text(rich_text_array):
    """Notionのリッチテキストを処理し、テキストを抽出"""
    extracted_texts = []
    
    for rt in rich_text_array:
        if "text" in rt:
            extracted_texts.append(rt["text"]["content"])
        elif "mention" in rt:  # Mention（ページリンク）
            if "page" in rt["mention"]:
                page_title = fetch_page_title(rt["mention"]["page"]["id"])
                if page_title:
                    extracted_texts.append(f"[{page_title}]")  # ページタイトルに置き換え
            else:
                print("Unknown mention type:", rt["mention"])
    
    return "".join(extracted_texts)

# === 指定されたNotionページIDのタイトルを取得 ===
def fetch_page_title(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        if "properties" in data and "名前" in data["properties"]:
            return data["properties"]["名前"]["title"][0]["text"]["content"]
    
    return None



# === トップページのHTMLを生成 ===
def generate_top_page(entries_by_date):
    """最新100トピックをトップページとしてHTMLに変換"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>最新のトピック</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
            h1 { color: #333; }
            .daily { margin-bottom: 20px; padding: 10px; border-bottom: 1px solid #ddd; }
            .topic { margin-left: 20px; }
            .date { font-size: 1.2em; font-weight: bold; }
            a { text-decoration: none; color: #007bff; }
        </style>
    </head>
    <body>
        <h1>最新のトピック</h1>
    """

    for date, entries in entries_by_date.items():
        html_content += f"<div class='daily'>\n<a href='{date}.html'><h2 class='date'>{date}</h2></a>\n"
        for entry in entries:
            topic = entry.get("topic", "トピックなし")
            content = entry.get("content", "")
            html_content += f"<div class='topic'><a href='{date}.html'><h3>{topic}</h3></a>\n<p>{content[:100]}{'...' if len(content) > 100 else ''}</p></div>\n"
        html_content += "</div>\n"
    
    html_content += "</body></html>"
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("トップページ (index.html) を作成しました")

# === メイン処理（最新のトピックを取得し、トップページを生成） ===
if __name__ == "__main__":
    latest_entries_by_date = fetch_latest_entries(limit=30)  # 直近30日分
    generate_top_page(latest_entries_by_date)
