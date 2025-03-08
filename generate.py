import requests
import json
import os
import re
from dotenv import load_dotenv
from collections import defaultdict

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
            text_elements = block[block_type].get("rich_text", []) if block_type in block else []
            text_content = "".join(t["text"]["content"] for t in text_elements if "text" in t).strip()
            
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

def generate_top_page(data):
    """トップページを生成する"""
    print("✅ トップページ生成")
    entries_by_date = defaultdict(list)
    
    for item in data.get("results", []):
        properties = item.get("properties", {})
        date = properties.get("日付", {}).get("date", {}).get("start", "")
        page_id = item.get("id", "")
        is_public = properties.get("公開", {}).get("checkbox", False)
        
        if not date or not is_public:
            continue  # 日付がない、または非公開ページの場合はスキップ
        
        # Notion ページの本文を取得し、トピック単位で整理
        topics = fetch_page_content(page_id)
        
        for topic in topics:
            hashtags_html = "".join(f"<li>{tag}</li>" for tag in topic["hashtags"])
            content_html = "".join(f"<p>{para}</p>" for para in topic["content"])
            entry_html = f"""
            <div class="topic">
                <h3>{topic["title"]}</h3>
                <div class="hashtags">
                    <ul>{hashtags_html}</ul>
                </div>
                <div class="content">
                    {content_html}
                </div>
            </div>
            """
            entries_by_date[date].append(entry_html)
    
    # HTML 全体を作成
    daily_entries = "".join(f"""
    <div class="daily">
        <h2>{date}</h2>
        {''.join(entries)}
    </div>
    """ for date, entries in sorted(entries_by_date.items(), reverse=True))
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>日記ブログ</title>
    </head>
    <body>
        <h1>サイトタイトル（未定）</h1>
        {daily_entries}
    </body>
    </html>
    """
    
    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ index.html を生成しました！")

if __name__ == "__main__":
    data = fetch_notion_data()
    if data:
        generate_top_page(data)
