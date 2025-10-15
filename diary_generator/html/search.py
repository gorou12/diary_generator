from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.util import utilities

log = logger.get_logger()


def generate():
    context = {
        "should_index": False,
        "description": "ごろうの日記をまとめたサイト。",
        "initial_month": None,
    }
    utilities.render_template(
        "search.html", context, f"{config.FILE_NAMES.OUTPUT_BASE_DIR_NAME}search.html"
    )

    log.info("✅ 検索ページを生成しました！")
