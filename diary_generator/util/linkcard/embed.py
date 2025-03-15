import re

import requests

from diary_generator.util import linkcard


def youtube(url: str):
    youtube_id_match = re.search(r"(?:v=|youtu.be/)([\w\-]+)", url)
    if not youtube_id_match:
        return f'<a href="{url}" target="_blank">{url}</a>'
    video_id = youtube_id_match.group(1)

    return f"""
    <div class="video-embed">
      <iframe width="100%" height="315"
        src="https://www.youtube.com/embed/{video_id}"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen>
      </iframe>
    </div>
    """


def niconico(url: str):
    nico_id_match = re.search(r"/watch/([a-z0-9]+)", url)
    if not nico_id_match:
        return f'<a href="{url}" target="_blank">{url}</a>'
    video_id = nico_id_match.group(1)

    return f"""
    <div class="video-embed">
      <iframe width="100%" height="315"
        src="https://embed.nicovideo.jp/watch/{video_id}"
        frameborder="0" allowfullscreen>
      </iframe>
    </div>
    """


def twitter(url: str):
    if url in linkcard.twitter_cache:
        print(f"✅ ツイートキャッシュヒット: {url}")
        return linkcard.twitter_cache.get(url).get(
            "html", f'<a href="{url}" target="_blank">{url}</a>'
        )

    oembed_url = f"https://publish.twitter.com/oembed?url={url}"
    try:
        response = requests.get(oembed_url, timeout=5)

        if response.status_code != 200:
            return f'<a href="{url}" target="_blank">{url}</a>'

        oembed_data = response.json()
        linkcard.twitter_cache[url] = oembed_data
        print(f"✅ ツイート取得: {url}")
        return oembed_data.get("html", f'<a href="{url}" target="_blank">{url}</a>')

    except Exception as e:
        print(f"⚠️ ツイート取得失敗: {url} - {e}")

    return f'<a href="{url}" target="_blank">{url}</a>'
