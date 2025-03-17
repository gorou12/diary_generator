import difflib
import json
import os
import shutil

from diary_generator.config.configuration import config
from diary_generator.logger import logger, notifylogger

default_log = logger.get_logger()
notify_log = notifylogger.get_logger()

old_file_path = config.FILE_NAMES.CACHE_PREVIOUS_DIARY_PATH
new_file_path = config.FILE_NAMES.CACHE_DIARY_PATH


def copy_previous_json():
    """
    指定されたJSONをバックアップする
    """
    if os.path.exists(new_file_path):
        shutil.copy(
            new_file_path,
            old_file_path,
        )
        default_log.info("✅Diary JSONコピー完了")


def diff_diary_json():
    """
    新旧のJSONのDIFFを取り、Discordに通知する
    """
    diff_results = []

    if not os.path.exists(old_file_path):
        notify_log.info("Diaryを新しくダウンロードしました")
        return

    with open(old_file_path, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    with open(new_file_path, "r", encoding="utf-8") as f:
        new_data = json.load(f)

    if not old_data or not new_data:
        notify_log.warning("差分を取ろうとしましたが、どちらかのJSONが空みたいです")
        return

    old_contents = {}
    for old_date in old_data:
        date = old_date.get("date")
        old_contents[date] = {}
        for topic in old_date.get("topics"):
            title: str = topic["title"]
            items: list = topic["content"] + topic["hashtags"]
            old_contents[date][title] = items

    new_contents = {}
    for new_date in new_data:
        date = new_date.get("date")
        new_contents[date] = {}
        for topic in new_date.get("topics"):
            title: str = topic["title"]
            items: list = topic["content"] + topic["hashtags"]
            new_contents[date][title] = items

    for o_date, o_value in old_contents.items():
        if o_date not in new_contents:
            diff_results.append(f"del: {o_date}")
            continue
        for o_title, o_contents in o_value.items():
            if o_title not in new_contents[o_date]:
                diff_results.append(f"del: {o_date} -> {o_title}")

    for n_date, n_value in new_contents.items():
        if n_date not in old_contents:
            diff_results.append(f"add: {n_date}")
            continue
        for n_title, n_contents in n_value.items():
            if n_title not in old_contents[n_date]:
                diff_results.append(f"add: {n_date} -> {n_title}")
                continue
            o_contents = old_contents[n_date][n_title]
            diff = list(difflib.unified_diff(o_contents, n_contents, lineterm=""))
            if diff:
                diff_results.append(
                    f"changed: {n_date} -> {n_title}\n```diff\n{'\n'.join(diff)}\n```"
                )

    if diff_results:
        notify_log.info("\n" + "\n".join(diff_results))
