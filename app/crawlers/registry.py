from app.crawlers.generic_gov import GenericGovCrawler
from app.crawlers.hangzhou_gov import HangzhouGovCrawler


class CrawlerRegistry:
    def __init__(self):
        self._registry = {
            "generic_gov": GenericGovCrawler,
            "hangzhou_gov": HangzhouGovCrawler,
        }

    def create(self, name: str, config):
        crawler = self._registry.get(name)
        if not crawler:
            raise ValueError(f"Unknown crawler: {name}")
        return crawler(config)


crawler_registry = CrawlerRegistry()
