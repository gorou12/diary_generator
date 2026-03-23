"""トピック名・エイリアス・スラッグ文字列の比較用正規化（NFKC + 空白の統一）。"""

import re
import unicodedata

_ws_re = re.compile(r"\s+")


def normalize_topic_key(s: str) -> str:
    if not s:
        return ""
    t = unicodedata.normalize("NFKC", s)
    t = t.replace("\u3000", " ")
    t = t.strip()
    t = _ws_re.sub(" ", t)
    return t
