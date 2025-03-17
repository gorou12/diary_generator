import difflib
import os
import shutil

from diary_generator.config.configuration import config
from diary_generator.logger import logger, notifylogger

default_log = logger.get_logger()
notify_log = notifylogger.get_logger()


def copy_previous_json():
    """
    指定されたJSONをバックアップする
    """
    if os.path.exists(config.FILE_NAMES.CACHE_DIARY_PATH):
        shutil.copy(
            config.FILE_NAMES.CACHE_DIARY_PATH,
            config.FILE_NAMES.CACHE_PREVIOUS_DIARY_PATH,
        )
        default_log.info("✅Diary JSONコピー完了")


def diff_diary_json():
    """
    新旧のJSONのDIFFを取り、Discordに通知する
    """
    if not os.path.exists(config.FILE_NAMES.CACHE_PREVIOUS_DIARY_PATH):
        notify_log.info("Diaryを新しくダウンロードしました")
        return

    with open(config.FILE_NAMES.CACHE_DIARY_PATH, "r", encoding="utf-8") as f:
        old = f.read()
        old_lines = str(old).strip().splitlines()

    with open(config.FILE_NAMES.CACHE_PREVIOUS_DIARY_PATH, "r", encoding="utf-8") as f:
        new = f.read()
        new_lines = str(new).strip().splitlines()

    if not old or not new:
        notify_log.warning("差分を取ろうとしましたが、どちらかのJSONが空みたいです")
        return

    diff = list(difflib.unified_diff(old_lines, new_lines))
    if not diff:
        default_log.info("差分はなかったので、投稿のNotifyをしませんでした")
        return
    notify_log.info(f"今回の更新差分です\n```diff\n{'\n'.join(diff)}\n```")
