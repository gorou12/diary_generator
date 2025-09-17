from diary_generator.config.configuration import config
from diary_generator.logger import logger
from diary_generator.models import DiaryEntry
from diary_generator.util import utilities

log = logger.get_logger()


def _paginate_by_topics(
    diary_entries: list[DiaryEntry], topics_per_page: int
) -> tuple[list[list[DiaryEntry]], int]:
    """
    トピック数ベースでページ分割する
    日付の途中でもトピック数制限に達したら次のページに移る
    1日のトピック数が制限を超える場合は、その日付を1つのページに含める
    """
    pages = []
    current_page = []
    current_topic_count = 0

    for entry in diary_entries:
        entry_topics = entry.topics

        # 現在のエントリのトピック数が制限を超える場合
        if current_topic_count + len(entry_topics) > topics_per_page and current_page:
            # 現在のページを保存して新しいページを開始
            pages.append(current_page)
            current_page = []
            current_topic_count = 0

        # エントリを現在のページに追加
        # 注意：1日のトピック数が制限を超える場合でも、その日付は1つのページに含まれる
        current_page.append(entry)
        current_topic_count += len(entry_topics)

    # 最後のページを追加
    if current_page:
        pages.append(current_page)

    total_pages = len(pages)
    return pages, total_pages


def generate(diary_entries: list[DiaryEntry]):
    output_dir = config.FILE_NAMES.OUTPUT_BASE_DIR_NAME

    # トピック数ベースでページ分割
    pages, total_pages = _paginate_by_topics(
        diary_entries, config.PAGINATE.INDEX_TOPICS
    )

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
            "title": "ぷちダイアリー（たぶん本家）",
            "should_index": True,
            "description": "ごろうの日記をまとめたサイト。",
            "entries": page_items,
            "pagination": pagination,
        }

        utilities.render_template("index.html", context, filename)

    log.info("✅ トップページ（トピック数ベースページネーション付き）を生成しました！")
