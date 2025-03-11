from . import contents, html, json
from .models import Config


def generate_all(config: Config):
    # 日記データの取得
    diary_entries = contents.get(config)

    html.index.generate(diary_entries, config)
    html.dates.list.generate(diary_entries, config)
    html.dates.detail.generate(diary_entries, config)
    html.topics.list.generate(diary_entries, config)
    html.topics.detail.generate(diary_entries, config)

    json.search.generate(diary_entries, config)
