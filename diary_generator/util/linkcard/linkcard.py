import re

from . import embed
from .ogp import fetch_data, generate_card


def create(contents: list[str], ogp_cache: dict) -> list[str]:
    return [_sub_link_card(content, ogp_cache) for content in contents]


def _sub_link_card(text: str, ogp_cache: dict) -> str:
    url_pattern = re.compile(r'(https?://[^\s<>"\'\)\]]+)')

    def replace_url(match):
        url = match.group(0)
        if "youtube.com" in url or "youtu.be" in url:
            return embed.youtube(url)
        elif "nicovideo.jp" in url:
            return embed.niconico(url)
        elif "twitter.com" in url:
            return embed.twitter(url)
        elif "x.com" in url:
            return embed.twitter(url)
        else:
            if url in ogp_cache:
                return generate_card(url, ogp_cache[url])
            else:
                ogp_data = fetch_data(url)
                if ogp_data:
                    ogp_cache[url] = ogp_data
                    return generate_card(url, ogp_data)
                else:
                    return f'<a href="{url}" target="_blank">{url}</a>'

    return url_pattern.sub(replace_url, text)
