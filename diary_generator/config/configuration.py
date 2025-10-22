from dataclasses import dataclass

from diary_generator.config import env, filenames, paginate


@dataclass(frozen=True)
class ThumbnailConfig:
    """サムネイル生成設定"""

    SMALL_SIZE: int = 380
    MEDIUM_SIZE: int = 520
    LARGE_SIZE: int = 720
    QUALITY: int = 85

    @property
    def sizes(self) -> dict[str, int]:
        """サムネイルサイズ辞書を返す"""
        return {
            "small": self.SMALL_SIZE,
            "medium": self.MEDIUM_SIZE,
            "large": self.LARGE_SIZE,
        }


@dataclass(frozen=True)
class Config:
    USE_CACHE: bool = False
    MAX_OGP_LEN: int = 90
    FILE_NAMES: filenames.FileName = filenames.FileName()
    PAGINATE: paginate.Paginte = paginate.Paginte()
    ENV: env.Env = env.Env()
    THUMBNAIL: ThumbnailConfig = ThumbnailConfig()

    def set_use_cache(self, val: bool):
        object.__setattr__(self, "USE_CACHE", val)


config = Config()


def set_use_cache(val: bool):
    config.set_use_cache(val)
