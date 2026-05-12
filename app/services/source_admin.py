from __future__ import annotations

import re
from urllib.parse import urlparse

import yaml

from app.config import SOURCES_DIR
from app.schemas import SourceCreateRequest, SourceView
from app.services.registry import source_registry


class SourceAdminService:
    def __init__(self) -> None:
        self.custom_dir = SOURCES_DIR / "custom"
        self.custom_dir.mkdir(parents=True, exist_ok=True)

    def create_source(self, request: SourceCreateRequest) -> list[SourceView]:
        base_url = self._resolve_base_url(request)
        key = self._resolve_key(request, base_url)
        payload = {
            "key": key,
            "name": request.name.strip(),
            "base_url": base_url,
            "region": request.region.strip(),
            "enabled": request.enabled,
            "crawler": request.crawler,
            "channels": [
                {
                    "name": channel.name.strip(),
                    "url": channel.url.strip(),
                    "item_selector": channel.item_selector.strip(),
                    "link_selector": channel.link_selector.strip(),
                    "list_date_selector": channel.list_date_selector.strip(),
                    "issuer": channel.issuer.strip(),
                }
                for channel in request.channels
            ],
        }

        file_path = self.custom_dir / f"{key}.yaml"
        with file_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)

        source_registry.load(force=True)
        return source_registry.list_sources()

    def _resolve_base_url(self, request: SourceCreateRequest) -> str:
        candidate = request.base_url.strip()
        if candidate:
            return candidate.rstrip("/")

        for channel in request.channels:
            channel_url = channel.url.strip()
            if not channel_url:
                continue
            parsed = urlparse(channel_url)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"

        raise ValueError("Base URL is missing and could not be inferred from channel URLs.")

    def _resolve_key(self, request: SourceCreateRequest, base_url: str) -> str:
        raw_key = request.key.strip()
        if not raw_key:
            raw_key = self._slug_from_name(request.name) or self._slug_from_domain(base_url)

        normalized = re.sub(r"[^a-z0-9_\-]+", "-", raw_key.lower()).strip("-")
        if len(normalized) < 3:
            normalized = self._slug_from_domain(base_url)
        if len(normalized) < 3:
            raise ValueError("Source key is too short.")

        existing = {item.key for item in source_registry.get_many([])}
        if normalized in existing:
            suffix = 2
            while f"{normalized}-{suffix}" in existing:
                suffix += 1
            normalized = f"{normalized}-{suffix}"

        return normalized

    def _slug_from_name(self, name: str) -> str:
        ascii_name = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
        return ascii_name

    def _slug_from_domain(self, base_url: str) -> str:
        host = urlparse(base_url).netloc.lower()
        host = host.replace("www.", "")
        slug = re.sub(r"[^a-z0-9]+", "-", host).strip("-")
        return slug[:48]


source_admin_service = SourceAdminService()
