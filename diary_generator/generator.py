from diary_generator import contents, filemaintenance, html, json


def generate_all():
    # 日記データの取得
    diary_entries = contents.get()

    filemaintenance.reflesh_files()
    filemaintenance.copy_static_files()

    html.index.generate(diary_entries)
    html.dates.list.generate(diary_entries)
    html.dates.detail.generate(diary_entries)
    html.topics.list.generate(diary_entries)
    html.topics.detail.generate(diary_entries)

    json.search.generate(diary_entries)
