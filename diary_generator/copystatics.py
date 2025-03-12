import shutil


def copy_static_files():
    shutil.copytree("static", "output", dirs_exist_ok=True)
    print("✅静的ファイルコピー完了！")
