from diary_generator.util.img.download_image import download_image
from diary_generator.util.img.thumbnail import get_thumbnail_path


def generate_image_tag(id: str, url: str, alt_text="") -> str:
    local_path = download_image(id, url)

    # サムネイルパスを取得
    small_thumbnail = get_thumbnail_path(id, "small")
    medium_thumbnail = get_thumbnail_path(id, "medium")

    # pictureタグでレスポンシブ画像を生成
    return f'''<a href="{local_path}" target="_blank">
  <picture>
    <source media="(max-width: 400px)" srcset="{small_thumbnail}" type="image/webp">
    <source media="(min-width: 401px)" srcset="{medium_thumbnail}" type="image/webp">
    <img class="embedimg" src="{medium_thumbnail}" alt="{alt_text}" loading="lazy">
  </picture>
</a>'''
