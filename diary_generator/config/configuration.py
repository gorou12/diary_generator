from dataclasses import dataclass

from diary_generator.config import env, filenames, paginate


@dataclass(frozen=True)
class Config:
    USE_CACHE: bool = False
    MAX_OGP_LEN: int = 90
    FILE_NAMES: filenames.FileName = filenames.FileName()
    PAGINATE: paginate.Paginte = paginate.Paginte()
    ENV: env.Env = env.Env()

    def set_use_cache(self, val: bool):
        object.__setattr__(self, "USE_CACHE", val)


config = Config()


def set_use_cache(val: bool):
    config.set_use_cache(val)
