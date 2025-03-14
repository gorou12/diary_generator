import configparser

import requests
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
config.read("config/settings.ini", encoding="utf-8")


def generate_card(url: str, ogp_data: dict) -> str:
    image_html = f'<img src="{ogp_data["image"]}" alt="">' if ogp_data["image"] else ""

    maxlen = config.getint("ogp", "MaxDescriptionLength", fallback=90)
    description = ogp_data["description"][0:maxlen] + (
        "..." if len(ogp_data["description"]) > maxlen else ""
    )

    return f"""
    <div class="link-card">
      <a href="{url}" target="_blank">
        {image_html}
        <div class="text">
          <div class="title">{ogp_data["title"]}</div>
          <div class="description">{description}</div>
          <div class="url">{url}</div>
        </div>
      </a>
    </div>
    """


def fetch_data(url: str) -> dict | None:
    """
    指定URLからOGP情報（タイトル, 説明, 画像URL）を取得
    """
    try:
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return None

        # 文字コード推測
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")

        ogp = {
            "title": soup.find("meta", property="og:title") or soup.find("title"),
            "description": soup.find("meta", property="og:description"),
            "image": soup.find("meta", property="og:image"),
        }

        return {
            "title": ogp["title"]["content"]
            if ogp["title"] and ogp["title"].has_attr("content")
            else (ogp["title"].text if ogp["title"] else ""),
            "description": ogp["description"]["content"] if ogp["description"] else "",
            "image": ogp["image"]["content"] if ogp["image"] else "",
        }
    except Exception as e:
        print(f"⚠️ OGP取得失敗: {url} - {e}")
        return None
