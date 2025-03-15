import json
import os

from diary_generator.config.configuration import config
from diary_generator.util import linkcard


def initialize():
    if os.path.exists(config.FILE_NAMES.CACHE_OGP_PATH):
        with open(config.FILE_NAMES.CACHE_OGP_PATH, "r", encoding="utf-8") as f:
            linkcard.ogp_cache = json.load(f)
    if os.path.exists(config.FILE_NAMES.CACHE_TWITTER_PATH):
        with open(config.FILE_NAMES.CACHE_TWITTER_PATH, "r", encoding="utf-8") as f:
            linkcard.oembed_cache = json.load(f)

    print("📁OGPキャッシュロード完了")
    return


def save_cache():
    with open(config.FILE_NAMES.CACHE_OGP_PATH, "w", encoding="utf-8") as f:
        json.dump(linkcard.ogp_cache, f, ensure_ascii=False, indent=2)
    with open(config.FILE_NAMES.CACHE_TWITTER_PATH, "w", encoding="utf-8") as f:
        json.dump(linkcard.oembed_cache, f, ensure_ascii=False, indent=2)
    print("📝OGPキャッシュセーブ完了")
