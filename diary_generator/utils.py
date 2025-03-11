import os

import dotenv
from jinja2 import Environment, FileSystemLoader

dotenv.load_dotenv()
env = Environment(loader=FileSystemLoader("templates"))


def getenv(key: str) -> str:
    return os.getenv(key)


def get_notion_database_id() -> str:
    return getenv("DATABASE_ID")


def get_notion_api_key() -> str:
    return getenv("NOTION_API_KEY")


def paginate_list(items: list, items_per_page=20) -> tuple[list[list], int]:
    """リストをページごとに分割"""
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    pages = [
        items[i * items_per_page : (i + 1) * items_per_page] for i in range(total_pages)
    ]
    return pages, total_pages


def render_template(template_name, context, output_path):
    """Jinja2テンプレートをレンダリングしてファイルに保存"""
    template = env.get_template(template_name)
    output_from_parsed_template = template.render(context)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # 出力先フォルダ作成
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_from_parsed_template)
