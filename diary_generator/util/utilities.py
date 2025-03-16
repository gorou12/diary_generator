from jinja2 import Environment, FileSystemLoader

from diary_generator.html import sidebar_content

env = Environment(loader=FileSystemLoader("templates"))


def paginate_list(items: list, items_per_page=20) -> tuple[list[list], int]:
    """リストをページごとに分割"""
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    pages = [
        items[i * items_per_page : (i + 1) * items_per_page] for i in range(total_pages)
    ]
    return pages, total_pages


def render_template(template_name: str, context: dict, output_path: str):
    """Jinja2テンプレートをレンダリングしてファイルに保存"""
    context["sidebar_content"] = sidebar_content
    template = env.get_template(template_name)
    output_from_parsed_template = template.render(context)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_from_parsed_template)
