from diary_generator.config.configuration import config
from diary_generator.util import utilities


def generate():
    context = {
        "sidebar_content": "",
    }
    utilities.render_template(
        "search.html", context, f"{config.FILE_NAMES.OUTPUT_BASE_DIR_NAME}search.html"
    )

    print("✅ 検索ページを生成しました！")
