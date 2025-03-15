from .configuration import Config
from . import configuration


def getConfig() -> Config:
    return configuration.config
