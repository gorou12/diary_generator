from jinja2 import Environment, FileSystemLoader

from diary_generator.html import sidebar_content

env = Environment(loader=FileSystemLoader("templates"))

# templates から呼べるトピックURL生成関数（後で差し替え可能）
_topic_url_fn = None


def set_topic_url_fn(fn):
    global _topic_url_fn
    _topic_url_fn = fn


def topic_url(title: str, page: int = 1) -> str:
    # fallback（古い形式）: /topics/<title>.html
    if _topic_url_fn is None:
        # ブラウザ側でエンコードされるので最低限動くが、slug導入後はset_topic_url_fnで差し替える
        return f"/topics/{title}.html" if page <= 1 else f"/topics/{title}.html"
    return _topic_url_fn(title, page)


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
    # templates から topic_url(...) で呼べるようにする
    context["topic_url"] = topic_url

    template = env.get_template(template_name)
    output_from_parsed_template = template.render(context)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_from_parsed_template)
