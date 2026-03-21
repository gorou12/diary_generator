import hashlib
import json
import os
import re
from dataclasses import dataclass
from urllib.parse import quote

from diary_generator.config.configuration import config


def _normalize_title(title: str) -> str:
    # できるだけ「見た目の違い」を吸収して、同じトピックなら同じ自動スラッグになるようにする
    t = title.strip()
    # 連続空白を1つに
    t = re.sub(r"\s+", " ", t)
    return t


def _auto_slug_from_title(title: str) -> str:
    norm = _normalize_title(title)
    h = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:10]
    return f"t-{h}"


@dataclass(frozen=True)
class TopicSlugRule:
    name: str
    slug: str
    aliases: list[str]


class TopicSlugResolver:
    """
    トピック名（見出し / ハッシュタグ）から canonical URL を決定する。
    - 手動スラッグ（辞書）があれば優先
    - なければタイトルから自動スラッグ（t-xxxxxxxxxx）を生成
    """

    def __init__(self):
        self._manual: dict[str, str] = {}  # normalized title/alias -> slug

        # 任意: cache/topic_slugs.json に辞書を置けるようにする
        # 形式:
        # [
        #   {"name": "鏡音レン", "slug": "kagamine-len", "aliases": ["レン", "Len"]}
        # ]
        path = getattr(config.FILE_NAMES, "CACHE_TOPIC_SLUGS_PATH", None)
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                for r in raw:
                    name = _normalize_title(r.get("name", ""))
                    slug = r.get("slug", "").strip().strip("/")
                    aliases = r.get("aliases", []) or []
                    if not name or not slug:
                        continue
                    self._manual[name] = slug
                    for a in aliases:
                        an = _normalize_title(a)
                        if an:
                            self._manual[an] = slug
            except Exception:
                # 辞書ファイルが壊れていても生成は止めない
                pass

    def auto_slug(self, title: str) -> str:
        return _auto_slug_from_title(title)

    def slug(self, title: str) -> str:
        norm = _normalize_title(title)
        return self._manual.get(norm) or _auto_slug_from_title(title)

    def url(self, title: str, page: int = 1) -> str:
        s = self.slug(title)
        if page <= 1:
            return f"/topics/{quote(s)}/"
        return f"/topics/{quote(s)}/page/{page}/"
