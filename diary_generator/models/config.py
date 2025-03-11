import configparser
import sys
from dataclasses import dataclass


@dataclass
class PageInformation:
    paginate: int


@dataclass
class Config:
    cache_file_name: str
    use_cache: bool
    indexpage: PageInformation
    topiclist: PageInformation
    datelist: PageInformation


def load_config(
    core_config_path: str, page_config_path: str, use_cache: bool
) -> Config:
    config_ini = configparser.ConfigParser()
    config_ini.read([core_config_path, page_config_path])

    cache_file_name = config_ini.get("settings", "CacheFileName", fallback="")

    if cache_file_name == "":
        print("Wrong Config (missing cache_file_name)", file=sys.stderr)
        exit(1)

    index_page_information = PageInformation(
        paginate=config_ini.getint("indexpage", "paginate", fallback=20)
    )
    topic_list_information = PageInformation(
        paginate=config_ini.getint("topiclist", "paginate", fallback=20)
    )
    date_list_information = PageInformation(
        paginate=config_ini.getint("datelist", "paginate", fallback=20)
    )

    return Config(
        cache_file_name=cache_file_name,
        use_cache=use_cache,
        indexpage=index_page_information,
        topiclist=topic_list_information,
        datelist=date_list_information,
    )
