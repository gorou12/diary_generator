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

def get_navigation(is_subpage=False):
    """ページごとの適切なナビゲーションを取得"""
    prefix = "../" if is_subpage else ""
    return f"""
    <nav>
        <ul>
            <li><a href="{prefix}index.html">トップページ</a></li>
            <li><a href="{prefix}topics.html">トピック一覧</a></li>
            <li><a href="{prefix}dates.html">日付一覧</a></li>
        </ul>
    </nav>
    """

def fetch_notion_data():
    """Notion API からページ一覧と本文を一括取得し、一時保存する"""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    
    if response.status_code == 200:
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
            all_pages.append({
                "date": date,
                "topics": topics
            })
        
        with open("data.json", "w", encoding="utf-8") as f:
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

def load_notion_data():
    """保存された Notion データを読み込む"""
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def generate_top_page(data):
    """トップページを生成する"""
    print("✅ トップページ生成")
    entries_by_date = defaultdict(list)
    
    for page in data:
        date = page["date"]
        for topic in page["topics"]:
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
        {get_navigation()}
        {daily_entries}
    </body>
    </html>
    """
    
    with open("output/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ index.html を生成しました！")

def generate_topic_pages(data):
    """トピックページを生成する"""
    print("✅ トピックページ生成")
    topic_dict = defaultdict(list)
    
    for page in data:
        date = page["date"]
        for topic in page["topics"]:
            topic_dict[topic["title"]].append((date, topic))
    
    for topic, entries in topic_dict.items():
        entries_html = "".join(f"""
        <div class="day">
            <h3>{date}</h3>
            <div class="hashtags">
                <ul>{''.join(f'<li>{tag}</li>' for tag in entry["hashtags"])}
                </ul>
            </div>
            <div class="content">
                {''.join(f'<p>{para}</p>' for para in entry["content"])}
            </div>
        </div>
        """ for date, entry in sorted(entries, reverse=True))
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <title>{topic}</title>
        </head>
        <body>
            <h1>サイトタイトル（未定）</h1>
            {get_navigation(is_subpage=True)}
            <h2>{topic}</h2>
            {entries_html}
        </body>
        </html>
        """
        os.makedirs("output/topics", exist_ok=True)
        with open(f"output/topics/{topic}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
    print("✅ トピックページを生成しました！")

def generate_date_pages(data):
    """日付ページを生成する"""
    print("✅ 日付ページ生成")
    os.makedirs("output/dates", exist_ok=True)
    
    for page in data:
        date = page["date"]
        entries_html = "".join(f"""
        <div class="topic">
            <h3>{topic["title"]}</h3>
            <div class="hashtags">
                <ul>{''.join(f'<li>{tag}</li>' for tag in topic["hashtags"])}
                </ul>
            </div>
            <div class="content">
                {''.join(f'<p>{para}</p>' for para in topic["content"])}
            </div>
        </div>
        """ for topic in page["topics"])
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <title>{date}</title>
        </head>
        <body>
            <h1>サイトタイトル（未定）</h1>
            {get_navigation(is_subpage=True)}
            <h2>{date}</h2>
            {entries_html}
        </body>
        </html>
        """
        
        with open(f"output/dates/{date}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
    print("✅ 日付ページを生成しました！")

def generate_topics_index(data):
    """トピック一覧ページを生成する"""
    print("✅ トピック一覧ページ生成")
    topics = set()
    for page in data:
        for topic in page["topics"]:
            topics.add(topic["title"])
    
    topics_html = "".join(f'<li><a href="topics/{topic}.html">{topic}</a></li>' for topic in sorted(topics))
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>トピック一覧</title>
    </head>
    <body>
        <h1>トピック一覧</h1>
        {get_navigation()}
        <ul>
            {topics_html}
        </ul>
    </body>
    </html>
    """
    
    with open("output/topics.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ トピック一覧ページを生成しました！")

def generate_dates_index(data):
    """日付一覧ページを生成する"""
    print("✅ 日付一覧ページ生成")
    dates = sorted({page["date"] for page in data}, reverse=True)
    
    dates_html = "".join(f'<li><a href="dates/{date}.html">{date}</a></li>' for date in dates)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>日付一覧</title>
    </head>
    <body>
        <h1>日付一覧</h1>
        {get_navigation()}
        <ul>
            {dates_html}
        </ul>
    </body>
    </html>
    """
    
    with open("output/dates.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ 日付一覧ページを生成しました！")

if __name__ == "__main__":
    data = fetch_notion_data()
    if data:
        generate_top_page(data)
        generate_topic_pages(data)
        generate_date_pages(data)
        generate_topics_index(data)
        generate_dates_index(data)