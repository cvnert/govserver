from abc import ABC, abstractmethod


class BaseCrawler(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def fetch_channel(self, channel: dict, limit: int = 10) -> list[dict]:
        raise NotImplementedError

