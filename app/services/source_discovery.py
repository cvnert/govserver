from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.crawlers.generic_gov import DEFAULT_HEADERS
from app.schemas import SourceDiscoverResponse, SourcePreviewItem
from app.utils import clean_text

import httpx


DATE_HINTS = ("date", "time", "pub", "day", "riqi", "sj")
CONTAINER_SELECTORS = [
    ".cont_right_list li",
    ".list li",
    ".news_list li",
    ".xxgk-list li",
    ".article-list li",
    ".listbox li",
    "ul li",
    "tbody tr",
]


class SourceDiscoveryService:
    def discover(self, url: str) -> SourceDiscoverResponse:
        html = self._get_text(url)
        soup = BeautifulSoup(html, "lxml")

        best = None
        for selector in CONTAINER_SELECTORS:
            previews = self._extract_previews(soup, url, selector)
            if len(previews) >= 3:
                date_selector = self._infer_date_selector(soup, selector)
                best = SourceDiscoverResponse(
                    item_selector=selector,
                    link_selector="a",
                    list_date_selector=date_selector,
                    previews=previews[:5],
                )
                break

        if not best:
            previews = self._extract_anchor_only(soup, url)
            best = SourceDiscoverResponse(
                item_selector="a",
                link_selector="a",
                list_date_selector="",
                previews=previews[:5],
            )

        return best

    def _extract_previews(self, soup: BeautifulSoup, base_url: str, selector: str) -> list[SourcePreviewItem]:
        previews: list[SourcePreviewItem] = []
        seen: set[str] = set()
        for node in soup.select(selector):
            link = node.select_one("a")
            if not link:
                continue
            href = link.get("href")
            title = clean_text(link.get_text(" ", strip=True))
            if not href or not title or href in seen or len(title) < 6:
                continue
            seen.add(href)
            previews.append(
                SourcePreviewItem(
                    title=title,
                    url=urljoin(base_url, href),
                    publish_time=self._extract_date_text(node),
                )
            )
        return previews

    def _extract_anchor_only(self, soup: BeautifulSoup, base_url: str) -> list[SourcePreviewItem]:
        previews: list[SourcePreviewItem] = []
        seen: set[str] = set()
        for link in soup.select("a"):
            href = link.get("href")
            title = clean_text(link.get_text(" ", strip=True))
            if not href or not title or href in seen or len(title) < 8:
                continue
            if href.startswith("javascript:") or href == "#":
                continue
            seen.add(href)
            previews.append(SourcePreviewItem(title=title, url=urljoin(base_url, href), publish_time=""))
            if len(previews) >= 5:
                break
        return previews

    def _infer_date_selector(self, soup: BeautifulSoup, item_selector: str) -> str:
        for node in soup.select(item_selector)[:5]:
            for child in node.find_all(True, recursive=True):
                attrs = " ".join(
                    [
                        child.name or "",
                        child.get("class", [""])[0] if child.get("class") else "",
                        child.get("id", ""),
                    ]
                ).lower()
                text = clean_text(child.get_text(" ", strip=True))
                if text and any(hint in attrs for hint in DATE_HINTS):
                    if child.name == "span":
                        return "span"
                    if child.get("class"):
                        return f".{child.get('class')[0]}"
                    if child.get("id"):
                        return f"#{child.get('id')}"
        return ""

    def _extract_date_text(self, node) -> str:
        for child in node.find_all(True, recursive=True):
            attrs = " ".join(
                [
                    child.name or "",
                    child.get("class", [""])[0] if child.get("class") else "",
                    child.get("id", ""),
                ]
            ).lower()
            text = clean_text(child.get_text(" ", strip=True))
            if text and any(hint in attrs for hint in DATE_HINTS):
                return text
        return ""

    def _get_text(self, url: str) -> str:
        with httpx.Client(timeout=20, follow_redirects=True, headers=DEFAULT_HEADERS) as client:
            response = client.get(url)
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            return response.text


source_discovery_service = SourceDiscoveryService()
