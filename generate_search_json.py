import json


def generate_search_data(data):
    """全文検索用の search_data.json を生成する"""
    print("🔄 本文検索用データ (search_data.json) を生成中...")

    search_items = []

    for page in data:
        date = page["date"]
        url = f"dates/{date}.html"  # 日付ページへのリンク

        for topic in page["topics"]:
            title = topic["title"]
            content_text = " ".join(topic["content"])  # 段落を結合して1つの文字列に
            hashtags = " ".join(
                f"#{tag}" for tag in topic["hashtags"]
            )  # ハッシュタグも含める
            full_content = f"{content_text} {hashtags}"  # 本文 + タグ

            search_items.append(
                {"date": date, "title": title, "content": full_content, "url": url}
            )

    # JSONファイルとして保存
    with open("output/search_data.json", "w", encoding="utf-8") as f:
        json.dump(search_items, f, ensure_ascii=False, indent=2)

    print(f"✅ search_data.json を {len(search_items)} 件生成しました！")
