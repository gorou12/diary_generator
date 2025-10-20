import os
import re

import requests

from diary_generator.logger import logger
from diary_generator.util.img.thumbnail import generate_all_thumbnails

log = logger.get_logger()


def download_image(id: str, url: str, save_dir="output/images") -> str:
    os.makedirs(save_dir, exist_ok=True)
    # filename = url.split("/")[-1].split("?")[0]  # URL末尾からファイル名抽出
    extension = url.split("/")[-1].split(".")[-1]
    extension = re.split("[?#]", extension)[0]
    filename = id + "." + extension
    save_path = os.path.join(save_dir, filename)

    # 既に存在すればダウンロード省略
    if not os.path.exists(save_path):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                log.info(f"✅ 画像保存: {save_path}")

                # サムネイル生成
                generate_all_thumbnails(save_path, id)
            else:
                log.warning(f"⚠️ 画像取得失敗: {url} --> {response.status_code}")
        except Exception as _:
            log.warning("⚠️ ダウンロード例外", exc_info=True)
    else:
        # 既存画像の場合もサムネイルが存在するかチェックして生成
        generate_all_thumbnails(save_path, id)

    # HTML用のパスを返す
    return f"/images/{filename}"
