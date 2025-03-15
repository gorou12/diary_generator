from diary_generator.util.img.download_image import download_image


def generate_image_tag(id: str, url: str, alt_text="") -> str:
    local_path = download_image(id, url)
    return f'<a href="{local_path}" target="_blank"><img class="embedimg" src="{local_path}" alt="{alt_text}" loading="lazy"></a>'
