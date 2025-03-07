import requests
import json
import os
from dotenv import load_dotenv

# === Notion APIの設定 ===
load_dotenv()
HTML_ROOT = os.getenv("HTML_ROOT") # HTMLファイルのルートパス
NOTION_API_KEY = os.getenv("NOTION_API_KEY")  # Notionのインテグレーションで取得
DATABASE_ID = os.getenv("DATABASE_ID")  # Notionの日記データベースID
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# === Notionのデータベースから指定日付のページを取得 ===
def fetch_notion_entries(date):
    """指定した日付の日記データをNotion APIから取得"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    # 日付のフィルタを修正（"日付" プロパティの date 型を考慮）
    data = {
        "filter": {
            "property": "日付",  # Notionでのプロパティ名
            "date": {
                "equals": date  # YYYY-MM-DD 形式
            }
        }
    }

    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code != 200:
        print(f"Error fetching data: {response.json()}")
        return []
    
    db_data = response.json()
    if "results" not in db_data or len(db_data["results"]) == 0:
        print(f"No entries found for {date}")
        return []
    
    page_id = db_data["results"][0]["id"]
    return fetch_page_blocks(page_id)

# === 各ページのブロックを取得（見出し・本文） ===
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
            # 新しいトピックが出たら、前のトピックを保存
            if current_topic:
                entries.append({"topic": current_topic, "content": "\n".join(current_content)})
                current_content = []
            current_topic = extract_rich_text(block["heading_3"]["rich_text"])
        
        elif block["type"] == "paragraph":
            if block["paragraph"]["rich_text"]:
                current_content.append(extract_rich_text(block["paragraph"]["rich_text"]))
    
    # 最後のトピックを追加
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

# === HTMLを生成 ===
def generate_html(date, entries):
    """指定した日付のデータをHTMLに変換"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{date} の日記</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
            h1 {{ color: #333; }}
            h2 {{ margin-top: 20px; color: #555; }}
            p {{ margin: 5px 0; }}
        </style>
    </head>
    <body>
        <h1>{date} の日記</h1>
    """
    
    for entry in entries:
        topic = entry.get("topic", "トピックなし")
        content = entry.get("content", "")
        html_content += f"<h2>{topic}</h2>\n<p>{content}</p>\n"
    
    html_content += "</body></html>"
    
    # ファイルに書き出し
    file_path = f"{HTML_ROOT}/{date}.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTMLファイルを作成しました: {file_path}")

# === メイン処理（指定した日付の日記を取得し、HTMLを作成） ===
if __name__ == "__main__":
    date = "2025-03-01"  # 取得したい日付（YYYY-MM-DD）
    entries = fetch_notion_entries(date)
    generate_html(date, entries)
