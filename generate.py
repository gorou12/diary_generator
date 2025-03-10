import argparse
import json
import os
import re
from collections import Counter, defaultdict

import requests
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

import generate_search_json

# .env ファイルを読み込む
load_dotenv()

# Jinja2テンプレートの読み込み
env = Environment(loader=FileSystemLoader("templates"))

# Notion API 設定
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

CACHE_FILE = "data.json"  # Notionデータの仮置き場所
ITEMS_PER_PAGE = 10  # 1ページに表示する最大数


def paginate_list(items, items_per_page=20):
    """リストをページごとに分割"""
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    pages = [
        items[i * items_per_page : (i + 1) * items_per_page] for i in range(total_pages)
    ]
    return pages, total_pages


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


def generate_top_page(data):
    """Jinja2でページネーション付きのトップページを生成"""
    print("✅ トップページ生成")
    pages, total_pages = paginate_list(data, items_per_page=20)

    for idx, page_items in enumerate(pages):
        page_num = idx + 1
        filename = (
            f"output/index_{page_num}.html" if page_num > 1 else "output/index.html"
        )

        # ページネーションリンク作成
        pagination = ""
        if page_num > 1:
            prev_link = "index.html" if page_num == 2 else f"index_{page_num - 1}.html"
            pagination += f'<a href="{prev_link}">« 前へ</a> '
        if page_num < total_pages:
            next_link = f"index_{page_num + 1}.html"
            pagination += f'<a href="{next_link}">次へ »</a>'

        # Jinja2 context
        context = {
            "title": "日記ブログ",
            "entries": page_items,
            "pagination": pagination,
            "sidebar_content": "",  # 必要ならサイドバー人気トピックなど
        }

        render_template("index.html", context, filename)

    print("✅ トップページ（ページネーション付き）を生成しました！")


def generate_topic_pages(data):
    """トピック/ハッシュタグごとの個別ページをJinja2で生成"""
    print("✅ トピックページ生成 (Jinja2)")
    os.makedirs("output/topics", exist_ok=True)

    topic_dict = defaultdict(list)
    hashtag_dict = defaultdict(list)

    # トピック・ハッシュタグの収集
    for page in data:
        date = page["date"]
        for topic in page["topics"]:
            topic_dict[topic["title"]].append((date, topic))
            for hashtag in topic["hashtags"]:
                hashtag_dict[hashtag].append((date, topic))

    # トピック＋ハッシュタグ統合
    combined_dict = {**topic_dict, **hashtag_dict}

    # 各トピックごとに生成
    for topic, entries in combined_dict.items():
        grouped_by_date = defaultdict(list)
        for date, entry in entries:
            grouped_by_date[date].append(entry)

        # Jinja2用コンテキスト準備
        context = {
            "title": f"トピック: {topic}",
            "topic_name": topic,
            "entries": [
                {
                    "date": f"{date[:4]}年{date[5:7]}月{date[8:10]}日",
                    "date_raw": date,
                    "entries": [
                        {
                            "title": entry["title"],
                            "hashtags": entry["hashtags"],
                            "content": entry["content"],
                        }
                        for entry in grouped_by_date[date]
                    ],
                }
                for date in sorted(grouped_by_date.keys(), reverse=True)
            ],
            "sidebar_content": "",  # 人気ランキングなど入れたい場合はここに
        }

        # ファイル出力
        output_file = f"output/topics/{topic}.html"
        render_template("topic.html", context, output_file)

    print("✅ トピックページ（ハッシュタグ含む）を生成しました！（Jinja2版）")


def generate_date_pages(data):
    """日付ページをJinja2で生成"""
    print("✅ 日付ページ生成")
    os.makedirs("output/dates", exist_ok=True)

    for page in data:
        date = page["date"]
        topics = page["topics"]
        # date_formatted = f"{date[:4]}年{date[5:7]}月{date[8:10]}日"  # YYYY-MM-DD → YYYY年MM月DD日
        context = {
            "title": f"日記 - {date}",
            "date": date,
            "topics": topics,  # [{'title': ..., 'content': [...], 'hashtags': [...]}, ...]
            "sidebar_content": "",  # 必要ならランキングなど入れる
        }
        output_file = f"output/dates/{date}.html"
        render_template("date.html", context, output_file)
    print("✅ 日付ページを生成しました！")


def generate_topics_index(data):
    """Jinja2でページネーション付きのトピック一覧を生成"""
    topic_counter = Counter()
    for page in data:
        for topic in page.get("topics", []):
            topic_counter[topic["title"]] += 1

    sorted_topics = topic_counter.most_common()
    popular_topics = [
        tpl for tpl in sorted_topics if tpl[1] >= 2
    ]  # Counterが2以上のものだけ

    pages, total_pages = paginate_list(sorted_topics, items_per_page=20)

    for idx, page_items in enumerate(pages):
        page_num = idx + 1
        filename = (
            f"output/topics_{page_num}.html" if page_num > 1 else "output/topics.html"
        )

        # ページネーションリンク作成
        pagination = ""
        if page_num > 1:
            prev_link = (
                "topics.html" if page_num == 2 else f"topics_{page_num - 1}.html"
            )
            pagination += f'<a href="{prev_link}">« 前へ</a> '
        if page_num < total_pages:
            next_link = f"topics_{page_num + 1}.html"
            pagination += f'<a href="{next_link}">次へ »</a>'

        # Jinja2 context
        context = {
            "title": "トピック一覧",
            "topics": page_items,
            "popular_topics": popular_topics[:10],
            "pagination": pagination,
            "sidebar_content": "",
        }
        render_template("topics.html", context, filename)

    print("✅ トピック一覧ページ（ページネーション付き）を生成しました！")


def generate_dates_index(data):
    """Jinja2でページネーション付きの日付一覧を生成"""
    print("✅ 日付一覧ページ生成")
    dates = sorted({page["date"] for page in data}, reverse=True)

    pages, total_pages = paginate_list(dates, items_per_page=20)

    for idx, page_items in enumerate(pages):
        page_num = idx + 1
        filename = (
            f"output/dates_{page_num}.html" if page_num > 1 else "output/dates.html"
        )

        # ページネーションリンク作成
        pagination = ""
        if page_num > 1:
            prev_link = "dates.html" if page_num == 2 else f"dates_{page_num - 1}.html"
            pagination += f'<a href="{prev_link}">« 前へ</a> '
        if page_num < total_pages:
            next_link = f"dates_{page_num + 1}.html"
            pagination += f'<a href="{next_link}">次へ »</a>'

        # Jinja2 context
        context = {
            "title": "日付一覧",
            "dates": page_items,
            "pagination": pagination,
            "sidebar_content": "",
        }
        render_template("dates.html", context, filename)

    print("✅ 日付一覧ページ（ページネーション付き）を生成しました！")


def render_template(template_name, context, output_path):
    """Jinja2テンプレートをレンダリングしてファイルに保存"""
    template = env.get_template(template_name)
    output_from_parsed_template = template.render(context)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # 出力先フォルダ作成
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_from_parsed_template)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-cache", action="store_true", help="キャッシュを使用する")
    args = parser.parse_args()

    data = fetch_notion_data(use_cache=args.use_cache)
    if data:
        print("✅ データ取得完了！")
        generate_top_page(data)
        generate_topic_pages(data)
        generate_date_pages(data)
        generate_topics_index(data)
        generate_dates_index(data)
        generate_search_json.generate_search_data(data)
