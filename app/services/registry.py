from dataclasses import dataclass
from pathlib import Path

import yaml

from app.config import SOURCES_DIR
from app.schemas import SourceView


@dataclass
class SourceConfig:
    key: str
    name: str
    base_url: str
    region: str
    enabled: bool
    crawler: str
    channels: list[dict]
    file_path: str


class SourceRegistry:
    def __init__(self, root: Path):
        self.root = root
        self._sources: dict[str, SourceConfig] = {}

    def load(self, force: bool = False) -> None:
        if self._sources and not force:
            return

        loaded: dict[str, SourceConfig] = {}
        for path in self.root.rglob("*.yaml"):
            with path.open("r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
            key = payload["key"]
            loaded[key] = SourceConfig(
                key=key,
                name=payload["name"],
                base_url=payload["base_url"],
                region=payload.get("region", ""),
                enabled=payload.get("enabled", True),
                crawler=payload.get("crawler", "generic_gov"),
                channels=payload.get("channels", []),
                file_path=str(path),
            )
        self._sources = loaded

    def list_sources(self) -> list[SourceView]:
        return [
            SourceView(
                key=item.key,
                name=item.name,
                base_url=item.base_url,
                region=item.region,
                enabled=item.enabled,
            )
            for item in self._sources.values()
        ]

    def get_many(self, keys: list[str] | None = None) -> list[SourceConfig]:
        if not keys:
            return [item for item in self._sources.values() if item.enabled]
        return [self._sources[key] for key in keys if key in self._sources]


source_registry = SourceRegistry(SOURCES_DIR)

