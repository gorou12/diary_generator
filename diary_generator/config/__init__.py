from . import configuration
from .configuration import Config


def getConfig() -> Config:
    return configuration.config
