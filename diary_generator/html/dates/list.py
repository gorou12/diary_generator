from ... import utils
from ...models import Config, DiaryEntry


def generate(diary_entries: list[DiaryEntry], config: Config):
    dates = sorted({diary_entry.date for diary_entry in diary_entries}, reverse=True)

    pages, total_pages = utils.paginate_list(dates, config.datelist.paginate)

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
        utils.render_template("dates.html", context, filename)

    print("✅ 日付一覧ページ（ページネーション付き）を生成しました！")
