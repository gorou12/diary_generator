#!/usr/bin/env python3
"""
既存画像のサムネイルを一括生成するスクリプト

使用方法:
    python scripts/generate_thumbnails.py
"""

import os
import sys
from pathlib import Path

from diary_generator.logger import logger
from diary_generator.util.img.thumbnail import generate_thumbnails_for_existing_images

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


log = logger.get_logger()


def main():
    """メイン処理"""
    log.info("🚀 既存画像のサムネイル一括生成を開始")

    images_dir = "output/images"

    if not os.path.exists(images_dir):
        log.error(f"❌ 画像ディレクトリが存在しません: {images_dir}")
        return 1

    # 画像ファイル数をカウント
    image_files = [
        f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f))
    ]
    log.info(f"📊 処理対象画像数: {len(image_files)}枚")

    # サムネイル生成実行
    processed_count = generate_thumbnails_for_existing_images(images_dir)

    log.info(f"✅ サムネイル一括生成完了: {processed_count}枚処理")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
