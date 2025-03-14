import re


def convert_contents_link_card(contents: list[str]) -> list[str]:
    return [_sub_link_card(content) for content in contents]


def _sub_link_card(text: str) -> str:
    url_pattern = re.compile(r'(https?://[^\s<>"\'\)\]]+)')
    return url_pattern.sub(
        r'<div class="link-card"><a href="\1" target="_blank"><p class="url">\1</p></a></div>',
        text,
    )
