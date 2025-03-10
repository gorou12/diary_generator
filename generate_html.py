import configparser
import os
from collections import Counter, defaultdict

from jinja2 import Environment, FileSystemLoader

config = configparser.ConfigParser()
config.read("config/page.ini")

# Jinja2テンプレートの読み込み
env = Environment(loader=FileSystemLoader("templates"))


def render_template(template_name, context, output_path):
    """Jinja2テンプレートをレンダリングしてファイルに保存"""
    template = env.get_template(template_name)
    output_from_parsed_template = template.render(context)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # 出力先フォルダ作成
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_from_parsed_template)


def generate_top_page(data):
    """Jinja2でページネーション付きのトップページを生成"""
    print("✅ トップページ生成")
    pages, total_pages = paginate_list(
        data, config.getint("indexpage", "paginate", fallback=20)
    )

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

    pages, total_pages = paginate_list(
        sorted_topics, config.getint("topiclist", "paginate", fallback=20)
    )

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

    pages, total_pages = paginate_list(
        dates, config.getint("datelist", "paginate", fallback=20)
    )

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


def paginate_list(items, items_per_page=20):
    """リストをページごとに分割"""
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    pages = [
        items[i * items_per_page : (i + 1) * items_per_page] for i in range(total_pages)
    ]
    return pages, total_pages
