import json
import os
from types import SimpleNamespace

from bs4 import BeautifulSoup

from diary_generator.config.configuration import config
from diary_generator.json import calendar, search
from diary_generator.models import DiaryEntry, IndexDirection, Topic


def use_tmp_json_output(tmp_path):
    original_file_names = config.FILE_NAMES
    json_dir = tmp_path / "json"
    json_dir.mkdir()
    object.__setattr__(
        config,
        "FILE_NAMES",
        SimpleNamespace(OUTPUT_JSON_DIR_NAME=f"{json_dir}{os.sep}"),
    )
    return original_file_names, json_dir


def diary_entry() -> DiaryEntry:
    return DiaryEntry(
        date="2026-01-15",
        date_jpn="2026年01月15日",
        index_direction=IndexDirection.INDEX,
        topics=[
            Topic(
                title="読書",
                id="topic-reading",
                content=["小説を読み終えた", "感想をメモした"],
                hashtags=["本", "メモ"],
            )
        ],
    )


def test_search_data_contains_body_and_hashtags(tmp_path):
    original_file_names, json_dir = use_tmp_json_output(tmp_path)
    try:
        search.generate([diary_entry()])
    finally:
        object.__setattr__(config, "FILE_NAMES", original_file_names)

    data = json.loads((json_dir / "search_data.json").read_text(encoding="utf-8"))

    assert data == [
        {
            "date": "2026-01-15",
            "title": "読書",
            "content": "小説を読み終えた 感想をメモした #本 #メモ",
            "url": "dates/2026-01-15.html",
        }
    ]


def test_calendar_data_contains_target_month_and_date_link(tmp_path):
    original_file_names, json_dir = use_tmp_json_output(tmp_path)
    try:
        calendar.generate([diary_entry()])
    finally:
        object.__setattr__(config, "FILE_NAMES", original_file_names)

    data = json.loads((json_dir / "calendar_data.json").read_text(encoding="utf-8"))
    soup = BeautifulSoup(data["calendars"]["2026-01"], "html.parser")
    link = soup.find("a", href="/dates/2026-01-15.html")

    assert data["available_months"] == ["2026-01"]
    assert link is not None
    assert link.get_text(strip=True) == "15"
