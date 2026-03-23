"""TopicSlugEntry から正規化キー → canonical slug の辞書を構築し、URL 解決を行う。"""

from __future__ import annotations

import hashlib
from urllib.parse import quote

from diary_generator.logger import logger
from diary_generator.models import TopicSlugEntry
from diary_generator.topic_slugs.normalize import normalize_topic_key

log = logger.get_logger()


def build_lookup(entries: list[TopicSlugEntry]) -> dict[str, str]:
    """
    正規化した名前・各エイリアス・スラッグ文字列をキーに canonical slug へマップする。
    同一キーに別 slug が割り当てられる場合は警告（後から処理したエントリが優先、後勝ち）。
    """
    out: dict[str, str] = {}
    for entry in entries:
        slug = entry.slug.strip().strip("/")
        if not slug:
            continue
        keys: list[str] = []
        nk = normalize_topic_key(entry.name)
        if nk:
            keys.append(nk)
        sk = normalize_topic_key(slug)
        if sk:
            keys.append(sk)
        for a in entry.aliases:
            ak = normalize_topic_key(a)
            if ak:
                keys.append(ak)

        for k in keys:
            prev = out.get(k)
            if prev is not None and prev != slug:
                log.warning(
                    "トピックスラッグの解決キーが衝突しました（後勝ち）: key=%r was=%r now=%r",
                    k,
                    prev,
                    slug,
                )
            out[k] = slug
    return out


def build_slug_to_display_name(entries: list[TopicSlugEntry]) -> dict[str, str]:
    """
    canonical slug（URL 用）→ Notion の正式名（名前）。
    同一 slug が複数レコードにあれば先に登場したエントリが優先（先勝ち）。
    """
    out: dict[str, str] = {}
    for entry in entries:
        slug = entry.slug.strip().strip("/")
        if not slug:
            continue
        name = entry.name.strip()
        if not name or slug in out:
            continue
        out[slug] = name
    return out


def auto_slug_from_title(title: str) -> str:
    """手動未登録トピック用。正規化キーを SHA1 に通した短い自動スラッグ。"""
    norm = normalize_topic_key(title)
    h = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:10]
    return f"t-{h}"


class TopicSlugResolver:
    """
    トピック名（見出し / ハッシュタグ）から canonical URL を決定する。
    データ取得は行わず、渡された lookup のみを使う（load 層で構築）。
    """

    def __init__(
        self,
        manual: dict[str, str],
        slug_to_display: dict[str, str] | None = None,
    ):
        self._manual = manual
        self._slug_to_display = slug_to_display or {}

    def display_name_for_slug(self, slug: str) -> str:
        """Notion に正式名があればそれを返す。無ければ slug をそのまま返す（自動 t-... 用）。"""
        return self._slug_to_display.get(slug, slug)

    def auto_slug(self, title: str) -> str:
        return auto_slug_from_title(title)

    def slug(self, title: str) -> str:
        norm = normalize_topic_key(title)
        return self._manual.get(norm) or auto_slug_from_title(title)

    def url(self, title: str, page: int = 1) -> str:
        s = self.slug(title)
        if page <= 1:
            return f"/topics/{quote(s)}/"
        return f"/topics/{quote(s)}/page/{page}/"
