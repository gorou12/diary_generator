from dataclasses import dataclass


@dataclass(frozen=True)
class TopicSlugEntry:
    """表示名・スラッグ・別名一覧"""

    name: str
    slug: str
    aliases: list[str]

    def to_dict(self) -> dict:
        return {"name": self.name, "slug": self.slug, "aliases": list(self.aliases)}

    @staticmethod
    def from_dict(d: dict) -> "TopicSlugEntry":
        aliases = d.get("aliases") or []
        return TopicSlugEntry(
            name=str(d.get("name", "")),
            slug=str(d.get("slug", "")),
            aliases=[str(a) for a in aliases] if isinstance(aliases, list) else [],
        )
