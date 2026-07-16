import re

from diary_generator.util import linkcard
from diary_generator.util.linkcard import embed
from diary_generator.util.linkcard.ogp import fetch_data, generate_card


def create(contents: list[str]) -> list[str]:
    return [_sub_link_card(content) for content in contents]


def _sub_link_card(text: str) -> str:
    preserved_html: list[str] = []

    def preserve_html(match):
        preserved_html.append(match.group(0))
        return f"<!--DIARY_GENERATOR_HTML_{len(preserved_html) - 1}-->"

    preserved_text = re.sub(
        r"<a\b[^>]*>.*?</a>|<[^>]+>",
        preserve_html,
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
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
        elif "bsky.app" in url:
            return embed.bluesky(url)
        elif "mstdn.pokete.com" in url:
            return embed.poketedon(url)
        else:
            if url in linkcard.ogp_cache:
                return generate_card(url, linkcard.ogp_cache[url])
            else:
                ogp_data = fetch_data(url)
                if ogp_data:
                    linkcard.ogp_cache[url] = ogp_data
                    return generate_card(url, ogp_data)
                else:
                    return f'<a href="{url}" target="_blank">{url}</a>'

    rendered = url_pattern.sub(replace_url, preserved_text)
    for index, html in enumerate(preserved_html):
        rendered = rendered.replace(f"<!--DIARY_GENERATOR_HTML_{index}-->", html)
    return rendered
