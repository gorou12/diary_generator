import requests
import json
import os
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

# === Notionのデータベースから日記を取得 ===
def fetch_notion_database():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    data = response.json()
    return data

# === 各ページのブロックを取得（見出し・本文） ===
def fetch_page_blocks(page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=HEADERS)
    return response.json()

# === データの整形（ページ一覧を取得） ===
def get_daily_entries():
    db_data = fetch_notion_database()

    if "results" not in db_data:
        print("Error: API response does not contain 'results'. Check API key and database ID.")
        return []

    entries = []
    for page in db_data["results"]:
        title = page["properties"]["名前"]["title"][0]["text"]["content"]  # タイトル（日付）
        page_id = page["id"]
        blocks = fetch_page_blocks(page_id)
        
        content = []
        for block in blocks["results"]:
            if block["type"] == "heading_3":
                # 見出しのリッチテキストが空でないことを確認
                if block["heading_3"]["rich_text"]:
                    text_content = extract_rich_text(block["heading_3"]["rich_text"])
                    content.append(f"## {text_content}")  # Markdown風の見出しに変換
            elif block["type"] == "paragraph":
                # 段落のリッチテキストが空でないことを確認
                if block["paragraph"]["rich_text"]:
                    text_content = extract_rich_text(block["paragraph"]["rich_text"])
                    content.append(text_content)
        
        entries.append({
            "date": title,
            "content": "\n".join(content)
        })
    
    return entries

def extract_rich_text(rich_text_array):
    """
    Notionのリッチテキストを処理し、テキストを抽出する関数。
    - mention（ページリンク）があれば、ページタイトルに置き換える or 削除。
    """
    extracted_texts = []
    
    for rt in rich_text_array:
        if "text" in rt:  # 通常のテキスト
            extracted_texts.append(rt["text"]["content"])
        elif "mention" in rt:  # Mention（別ページリンク）
            if "page" in rt["mention"]:  # ページのメンション
                page_id = rt["mention"]["page"]["id"]
                page_title = fetch_page_title(page_id)  # 別ページのタイトルを取得
                if page_title:
                    extracted_texts.append(f"[{page_title}]")  # 置き換え
                # 置き換えたくない場合は、ここでスキップしてもOK
            else:
                print("Unknown mention type:", rt["mention"])
    
    return "".join(extracted_texts)

def fetch_page_title(page_id):
    """
    指定されたNotionページIDのタイトルを取得する
    """
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if "properties" in data and "名前" in data["properties"]:
            return data["properties"]["名前"]["title"][0]["text"]["content"]
    
    return None  # タイトルが取得できない場合は None を返す


# === 実行してデータを取得 ===
if __name__ == "__main__":
    daily_entries = get_daily_entries()
    for entry in daily_entries:
        print(f"📅 {entry['date']}\n{entry['content']}\n{'='*40}")
