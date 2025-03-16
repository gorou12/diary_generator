from diary_generator.config.configuration import config
from diary_generator.models import DiaryEntry
from diary_generator.util import utilities


def generate(diary_entries: list[DiaryEntry]):
    output_dir = config.FILE_NAMES.OUTPUT_BASE_DIR_NAME
    pages, total_pages = utilities.paginate_list(diary_entries, config.PAGINATE.INDEX)

    for idx, page_items in enumerate(pages):
        page_num = idx + 1
        filename = (
            f"{output_dir}index_{page_num}.html"
            if page_num > 1
            else f"{output_dir}index.html"
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
        }

        utilities.render_template("index.html", context, filename)

    print("✅ トップページ（ページネーション付き）を生成しました！")
