from diary_generator import contents, filemaintenance, html, json
from diary_generator.topic_slug import TopicSlugResolver
from diary_generator.util import utilities


def generate_all():
    # 日記データの取得
    diary_entries = contents.get()

    # スラッグデータの取得
    resolver = TopicSlugResolver()
    utilities.set_topic_url_fn(resolver.url_for_title)

    filemaintenance.reflesh_files()
    filemaintenance.copy_static_files()

    html.index.generate(diary_entries)
    html.dates.list.generate(diary_entries)
    html.dates.detail.generate(diary_entries)
    html.topics.list.generate(diary_entries)
    html.topics.detail.generate(diary_entries, resolver)
    html.search.generate()

    json.search.generate(diary_entries)
    json.calendar.generate(diary_entries)
