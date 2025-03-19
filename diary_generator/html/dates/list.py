from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry
from diary_generator.util import utilities

log = logger.get_logger()


def generate(diary_entries: list[DiaryEntry]):
    output_dir = config.FILE_NAMES.OUTPUT_BASE_DIR_NAME
    dates = sorted({diary_entry.date for diary_entry in diary_entries}, reverse=True)

    pages, total_pages = utilities.paginate_list(dates, config.PAGINATE.DATE_LIST)

    for idx, page_items in enumerate(pages):
        page_num = idx + 1
        filename = (
            f"{output_dir}dates_{page_num}.html"
            if page_num > 1
            else f"{output_dir}dates.html"
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
            "should_index": False,
            "dates": page_items,
            "pagination": pagination,
        }
        utilities.render_template("dates.html", context, filename)

    log.info("✅ 日付一覧ページ（ページネーション付き）を生成しました！")
