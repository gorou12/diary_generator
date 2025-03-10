import argparse

from dotenv import load_dotenv

import generate_html
import generate_search_json
import get_diary_contents

# .env ファイルを読み込む
load_dotenv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-cache", action="store_true", help="キャッシュを使用する")
    args = parser.parse_args()

    data = get_diary_contents.fetch_notion_data(use_cache=args.use_cache)
    if data:
        print("✅ データ取得完了！")
        generate_html.generate_top_page(data)
        generate_html.generate_topic_pages(data)
        generate_html.generate_date_pages(data)
        generate_html.generate_topics_index(data)
        generate_html.generate_dates_index(data)
        generate_search_json.generate_search_data(data)
