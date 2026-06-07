import os

from PIL import Image, ImageOps

from diary_generator.config.configuration import config
from diary_generator.logger import logger

log = logger.get_logger()


def generate_thumbnail(
    original_path: str, output_path: str, max_width: int, quality: int = None
) -> bool:
    """
    指定された画像からサムネイルを生成する

    Args:
        original_path: 元画像のパス
        output_path: サムネイルの出力パス
        max_width: 最大幅（ピクセル）
        quality: WebP品質（1-100、Noneの場合は設定値を使用）

    Returns:
        bool: 生成成功時True
    """
    try:
        # 出力ディレクトリを作成
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 品質設定（Noneの場合は設定値を使用）
        if quality is None:
            quality = config.THUMBNAIL.QUALITY

        with Image.open(original_path) as img:
            # EXIF回転を適用
            img = ImageOps.exif_transpose(img)

            # アスペクト比を保持してリサイズ
            img.thumbnail((max_width, max_width), Image.Resampling.LANCZOS)

            # WebP形式で保存
            img.save(output_path, "WEBP", quality=quality, optimize=True)

        log.info(f"✅ サムネイル生成: {output_path}")
        return True

    except Exception as e:
        log.warning(f"⚠️ サムネイル生成失敗: {original_path} -> {output_path}: {e}")
        return False


def generate_all_thumbnails(
    original_path: str, image_id: str, base_dir: str = "output"
) -> dict:
    """
    画像から3サイズのサムネイルを生成する

    Args:
        original_path: 元画像のパス
        image_id: 画像ID（ファイル名から拡張子を除いた部分）
        base_dir: ベースディレクトリ

    Returns:
        dict: 生成されたサムネイルのパス辞書
    """
    thumbnails = {}

    # 設定からサムネイルサイズを取得
    sizes = config.THUMBNAIL.sizes

    for size_name, max_width in sizes.items():
        output_path = os.path.join(
            base_dir, "thumbnails", size_name, f"{image_id}.webp"
        )

        if generate_thumbnail(original_path, output_path, max_width):
            thumbnails[size_name] = f"/thumbnails/{size_name}/{image_id}.webp"

    return thumbnails


def get_thumbnail_path(
    image_id: str, size: str = "medium", base_dir: str = "output"
) -> str:
    """
    サムネイルのパスを取得する（存在しない場合は元画像パスを返す）

    Args:
        image_id: 画像ID
        size: サムネイルサイズ（'small' または 'medium' または 'large'）
        base_dir: ベースディレクトリ

    Returns:
        str: サムネイルのパス
    """
    thumbnail_path = os.path.join(base_dir, "thumbnails", size, f"{image_id}.webp")

    if os.path.exists(thumbnail_path):
        return f"/thumbnails/{size}/{image_id}.webp"
    else:
        # サムネイルが存在しない場合は元画像のパスを返す
        return f"/images/{image_id}"


def generate_thumbnails_if_missing(
    original_path: str, image_id: str, base_dir: str = "output"
) -> dict:
    """
    サムネイルが存在しない場合のみ生成する

    Args:
        original_path: 元画像のパス
        image_id: 画像ID（ファイル名から拡張子を除いた部分）
        base_dir: ベースディレクトリ

    Returns:
        dict: 生成されたサムネイルのパス辞書
    """
    thumbnails = {}

    # 設定からサムネイルサイズを取得
    sizes = config.THUMBNAIL.sizes

    for size_name, max_width in sizes.items():
        output_path = os.path.join(
            base_dir, "thumbnails", size_name, f"{image_id}.webp"
        )

        # サムネイルが存在しない場合のみ生成
        if not os.path.exists(output_path):
            if generate_thumbnail(original_path, output_path, max_width):
                thumbnails[size_name] = f"/thumbnails/{size_name}/{image_id}.webp"
        else:
            # 既存のサムネイルのパスを返す
            thumbnails[size_name] = f"/thumbnails/{size_name}/{image_id}.webp"

    return thumbnails


def generate_thumbnails_for_existing_images(images_dir: str = "output/images") -> int:
    """
    既存画像のサムネイルを一括再生成する（手動実行用）
    画質変更やサムネイルサイズ変更時の再生成用

    Args:
        images_dir: 画像ディレクトリのパス

    Returns:
        int: 処理した画像数
    """
    if not os.path.exists(images_dir):
        log.warning(f"⚠️ 画像ディレクトリが存在しません: {images_dir}")
        return 0

    processed_count = 0

    for filename in os.listdir(images_dir):
        if not os.path.isfile(os.path.join(images_dir, filename)):
            continue

        # ファイル名から画像IDを抽出（拡張子を除く）
        image_id = os.path.splitext(filename)[0]
        original_path = os.path.join(images_dir, filename)

        # サムネイルを強制的に再生成（既存でも上書き）
        thumbnails = generate_all_thumbnails(original_path, image_id)

        if thumbnails:
            processed_count += 1
            log.info(f"✅ 再生成完了: {filename} -> {len(thumbnails)}個のサムネイル")
        else:
            log.warning(f"⚠️ 再生成失敗: {filename}")

    log.info(f"📊 一括サムネイル再生成完了: {processed_count}枚処理")
    return processed_count
