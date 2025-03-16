import re

import requests

from diary_generator.logger import logger
from diary_generator.util import linkcard

log = logger.get_logger()


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
    if url in linkcard.oembed_cache:
        log.info(f"✅ ツイートキャッシュヒット: {url}")
        return linkcard.oembed_cache.get(url).get(
            "html", f'<a href="{url}" target="_blank">{url}</a>'
        )

    oembed_url = f"https://publish.twitter.com/oembed?url={url}"
    try:
        response = requests.get(oembed_url, timeout=5)

        if response.status_code != 200:
            return f'<a href="{url}" target="_blank">{url}</a>'

        oembed_data = response.json()
        linkcard.oembed_cache[url] = oembed_data
        log.info(f"✅ ツイート取得: {url}")
        return oembed_data.get("html", f'<a href="{url}" target="_blank">{url}</a>')

    except Exception as _:
        log.warning(f"⚠️ ツイート取得失敗: {url}", exc_info=True)

    return f'<a href="{url}" target="_blank">{url}</a>'


def bluesky(url: str):
    if url in linkcard.oembed_cache:
        log.info(f"✅ ポストキャッシュヒット: {url}")
        return linkcard.oembed_cache.get(url).get(
            "html", f'<a href="{url}" target="_blank">{url}</a>'
        )

    oembed_url = f"https://embed.bsky.app/oembed?url={url}"
    try:
        response = requests.get(oembed_url, timeout=5)

        if response.status_code != 200:
            return f'<a href="{url}" target="_blank">{url}</a>'

        oembed_data = response.json()
        linkcard.oembed_cache[url] = oembed_data
        log.info(f"✅ ポスト取得: {url}")
        return oembed_data.get("html", f'<a href="{url}" target="_blank">{url}</a>')

    except Exception as _:
        log.warning(f"⚠️ ポスト取得失敗: {url}", exc_info=True)

    return f'<a href="{url}" target="_blank">{url}</a>'


def poketedon(url: str):
    if url in linkcard.oembed_cache:
        log.info(f"✅ トゥートキャッシュヒット: {url}")
        return linkcard.oembed_cache.get(url).get(
            "html", f'<a href="{url}" target="_blank">{url}</a>'
        )

    oembed_url = f"https://mstdn.pokete.com/api/oembed?url={url}"
    try:
        response = requests.get(oembed_url, timeout=5)

        if response.status_code != 200:
            return f'<a href="{url}" target="_blank">{url}</a>'

        oembed_data = response.json()
        linkcard.oembed_cache[url] = oembed_data
        log.info(f"✅ トゥート取得: {url}")
        return oembed_data.get("html", f'<a href="{url}" target="_blank">{url}</a>')

    except Exception as _:
        log.warning(f"⚠️ トゥート取得失敗: {url}", exc_info=True)

    return f'<a href="{url}" target="_blank">{url}</a>'


# TODO: https://oembed.com/providers.json みたいなのを作ったらいい
# (そのまま読み込んでも絶対無駄が多い＆Mastodonが無いので、configあたりにお手製で作ったほうがいい)
