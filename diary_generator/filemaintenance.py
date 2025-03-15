import glob
import os
import shutil

from diary_generator.config.configuration import config


def reflesh_files():
    """
    output内のHTMLとJSONを全削除する
    画像は残しておく
    キャッシュ用フォルダは消さない
    """
    output_dir = config.FILE_NAMES.OUTPUT_BASE_DIR_NAME
    for html in glob.glob(f"{output_dir}**/*.html", recursive=True):
        if os.path.isfile(html):
            os.remove(html)
    for json in glob.glob(f"{output_dir}**/*.json", recursive=True):
        if os.path.isfile(json):
            os.remove(json)


def copy_static_files():
    """
    output/staticを作り直す
    """
    shutil.rmtree(config.FILE_NAMES.OUTPUT_STATIC_FILES_DIR_NAME)
    shutil.copytree(
        config.FILE_NAMES.STATIC_FILES_DIR_NAME,
        config.FILE_NAMES.OUTPUT_STATIC_FILES_DIR_NAME,
        dirs_exist_ok=True,
    )
    print("✅静的ファイルコピー完了！")
