import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FileName:
    CACHE_DIR_NAME: str = "cache/"

    CACHE_DIARY_PATH: str = f"{CACHE_DIR_NAME}diary_data.json"
    CACHE_PREVIOUS_DIARY_PATH: str = f"{CACHE_DIR_NAME}diary_data_prev.json"
    CACHE_OGP_PATH: str = f"{CACHE_DIR_NAME}ogp.json"
    CACHE_TWITTER_PATH: str = f"{CACHE_DIR_NAME}twitter.json"

    STATIC_FILES_DIR_NAME: str = "static/"

    LOG_DIR_NAME: str = "logs/"

    OUTPUT_BASE_DIR_NAME: str = "output/"
    OUTPUT_DATES_DIR_NAME: str = f"{OUTPUT_BASE_DIR_NAME}dates/"
    OUTPUT_TOPICS_DIR_NAME: str = f"{OUTPUT_BASE_DIR_NAME}topics/"
    OUTPUT_STATIC_FILES_DIR_NAME: str = f"{OUTPUT_BASE_DIR_NAME}src/"
    OUTPUT_IMAGE_DIR_NAME: str = f"{OUTPUT_BASE_DIR_NAME}images/"
    OUTPUT_JSON_DIR_NAME: str = f"{OUTPUT_BASE_DIR_NAME}json/"

    def __post_init__(self):
        os.makedirs(self.CACHE_DIR_NAME, exist_ok=True)
        # STATIC_FILES_DIR_NAMEはプロジェクトフォルダなので作らない
        os.makedirs(self.LOG_DIR_NAME, exist_ok=True)
        os.makedirs(self.CACHE_DIR_NAME, exist_ok=True)
        os.makedirs(self.OUTPUT_BASE_DIR_NAME, exist_ok=True)
        os.makedirs(self.OUTPUT_DATES_DIR_NAME, exist_ok=True)
        os.makedirs(self.OUTPUT_TOPICS_DIR_NAME, exist_ok=True)
        os.makedirs(self.OUTPUT_STATIC_FILES_DIR_NAME, exist_ok=True)
        os.makedirs(self.OUTPUT_IMAGE_DIR_NAME, exist_ok=True)
        os.makedirs(self.OUTPUT_JSON_DIR_NAME, exist_ok=True)
