import shutil


def copy_static_files():
    shutil.copytree("static", "output/src", dirs_exist_ok=True)
    print("✅静的ファイルコピー完了！")
