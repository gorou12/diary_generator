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

# === 全日記データを取得（例: 直近30日分） ===
def fetch_all_entries(limit=None):
    """全トピックをNotion APIから取得し、日付ごとに整理"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    today = datetime.today().strftime("%Y-%m-%d")
    thirty_days_ago = None  # すべてのデータを取得する場合はフィルタを外す

    data = {
        "filter": {"property": "日付", "date": {"is_not_empty": True}},
        "sorts": [
            {"property": "日付", "direction": "descending"}  # 新しい順にソート
        ],
        "page_size": 100,  # 最大100件取得
    }

    entries = {}
    start_cursor = ""

    while True:
        if start_cursor:
            data["start_cursor"] = start_cursor
        
        response = requests.post(url, headers=HEADERS, json=data)
        if response.status_code != 200:
            print(f"Error fetching data: {response.json()}")
            break

        db_data = response.json()
        results = db_data.get("results", [])
        
        for page in results:
            date = page["properties"]["日付"]["date"]["start"]
            page_id = page["id"]
            page_entries = fetch_page_blocks(page_id)
            
            for entry in page_entries:
                topic = entry["topic"]
                if topic not in entries:
                    entries[topic] = []
                entries[topic].append({"date": date, "content": entry["content"]})
        
        start_cursor = db_data.get("next_cursor")
        if not start_cursor:
            break
    
    return entries

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
                entries.append({"topic": current_topic, "content": "\n\n".join(current_content)})
                current_content = []
            current_topic = extract_rich_text(block["heading_3"]["rich_text"])
        
        elif block["type"] == "paragraph":
            if block["paragraph"]["rich_text"]:
                # print(block["paragraph"]["rich_text"])
                content = extract_rich_text(block["paragraph"]["rich_text"])
                if content:
                    current_content.append(content)
                    # current_content.append('\n')
    
    if current_topic:
        entries.append({"topic": current_topic, "content": "\n\n".join(current_content)})
    
    # print(entries)
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


# === トピックごとのHTMLを生成 ===
def generate_topic_pages(topics):
    """トピックごとにHTMLページを作成"""
    for topic, entries in topics.items():
        # ファイル名をトピック名から生成（半角英数字のみを許可）
        topic_filename = "".join(c if c.isalnum() else "_" for c in topic) + ".html"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{topic}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
                h1 {{ color: #333; }}
                .entry {{ margin-bottom: 20px; padding: 10px; border-bottom: 1px solid #ddd; }}
                .date {{ font-size: 1.2em; font-weight: bold; }}
                a {{ text-decoration: none; color: #007bff; }}
            </style>
        </head>
        <body>
            <h1>{topic}</h1>
        """

        for entry in sorted(entries, key=lambda x: x["date"], reverse=True):  # 新しい順
            date = entry["date"]
            content = entry["content"]
            formatted_content_array = []
            for paragraph in content.split("\n\n"):
                breaked_paragraph = paragraph.strip().replace("\n","<br>")
                formatted_content_array.append(f'<p>{breaked_paragraph}</p>')
            formatted_content = ''.join(formatted_content_array)
            html_content += f"""
                <div class="entry">
                    <a href="{date}.html"><h2 class="date">{date}</h2></a>
                    {formatted_content}
                </div>
            """

        html_content += "</body></html>"

        with open(topic_filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"トピックページ {topic_filename} を作成しました")

# === メイン処理（トピックごとにページを生成） ===
if __name__ == "__main__":
    topics = fetch_all_entries(limit=30)  # 直近30日分
    generate_topic_pages(topics)
