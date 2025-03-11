from .. import utils
from ..models import Config, DiaryEntry


def generate(diary_entries: list[DiaryEntry], config: Config):
    pages, total_pages = utils.paginate_list(diary_entries, config.indexpage.paginate)

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

        utils.render_template("index.html", context, filename)

    print("✅ トップページ（ページネーション付き）を生成しました！")
