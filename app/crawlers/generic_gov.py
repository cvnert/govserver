from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.crawlers.base import BaseCrawler
from app.utils import clean_text


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

MAIN_CONTENT_SELECTORS = [
    ".article",
    ".newscontent",
    ".news_content",
    ".article-content",
    ".detail-content",
    ".detailContent",
    ".content-main",
    ".main-content",
    "#zoom",
    ".TRS_Editor",
    ".content",
    ".art_content",
    "[id*='content']",
    "[class*='newscontent']",
    "[class*='content']",
    "[class*='detail']",
    "[class*='article']",
]

TITLE_SELECTORS = [
    "meta[name='ArticleTitle']",
    ".title",
    ".newstitle",
    "h1",
    ".article-title",
    "[class*='title']",
]

DATE_SELECTORS = [
    "meta[name='PubDate']",
    ".ly .day",
    ".pubdate",
    ".info span",
    "[class*='date']",
]

SOURCE_SELECTORS = [
    "meta[name='ContentSource']",
    ".ly .laiy",
    "[class*='source']",
]


class GenericGovCrawler(BaseCrawler):
    main_content_selectors = MAIN_CONTENT_SELECTORS
    title_selectors = TITLE_SELECTORS
    date_selectors = DATE_SELECTORS
    source_selectors = SOURCE_SELECTORS

    def fetch_channel(self, channel: dict, limit: int = 10) -> list[dict]:
        html = self._get_text(channel["url"])
        soup = BeautifulSoup(html, "lxml")

        item_selector = channel.get("item_selector")
        link_selector = channel.get("link_selector", "a")
        date_selector = channel.get("list_date_selector")

        items: list[dict] = []
        seen: set[str] = set()

        nodes = soup.select(item_selector) if item_selector else soup.select(link_selector)
        for node in nodes:
            link_node = node.select_one(link_selector) if item_selector else node
            if not link_node:
                continue

            href = link_node.get("href")
            if not href or href in seen:
                continue
            seen.add(href)

            detail_url = urljoin(channel["url"], href)
            detail_data = self._parse_detail_page(detail_url)

            title = detail_data["title"] or clean_text(link_node.get_text(" ", strip=True))
            content_clean = detail_data["content_clean"]

            if not title or not content_clean:
                continue

            publish_time = detail_data["publish_time"]
            if not publish_time and item_selector and date_selector:
                date_node = node.select_one(date_selector)
                if date_node:
                    publish_time = clean_text(date_node.get_text(" ", strip=True))

            items.append(
                {
                    "title": title,
                    "url": detail_url,
                    "channel": channel.get("name", ""),
                    "issuer": detail_data["issuer"] or channel.get("issuer", ""),
                    "publish_time": publish_time,
                    "summary": content_clean[:180],
                    "content_raw": detail_data["content_raw"],
                    "content_clean": content_clean,
                }
            )

            if len(items) >= limit:
                break

        return items

    def _parse_detail_page(self, url: str) -> dict:
        detail_html = self._get_text(url)
        detail_soup = BeautifulSoup(detail_html, "lxml")

        title = self._extract_text_by_selectors(detail_soup, self.title_selectors)
        publish_time = self._extract_meta_or_text(detail_soup, self.date_selectors)
        issuer = self._extract_meta_or_text(detail_soup, self.source_selectors)

        content_node = None
        for selector in self.main_content_selectors:
            candidate = detail_soup.select_one(selector)
            if candidate and clean_text(candidate.get_text("\n", strip=True)):
                content_node = candidate
                break

        content_raw = content_node.get_text("\n", strip=True) if content_node else ""
        content_clean = clean_text(content_raw)
        return {
            "title": title,
            "publish_time": publish_time,
            "issuer": issuer,
            "content_raw": content_raw,
            "content_clean": content_clean,
        }

    @staticmethod
    def _extract_text_by_selectors(soup: BeautifulSoup, selectors: list[str]) -> str:
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                if node.name == "meta":
                    text = clean_text(node.get("content", ""))
                    if text:
                        return text
                text = clean_text(node.get_text(" ", strip=True))
                if text:
                    return text
        return clean_text(soup.title.get_text(" ", strip=True)) if soup.title else ""

    @staticmethod
    def _extract_meta_or_text(soup: BeautifulSoup, selectors: list[str]) -> str:
        for selector in selectors:
            node = soup.select_one(selector)
            if not node:
                continue
            if node.name == "meta":
                content = clean_text(node.get("content", ""))
                if content:
                    return content
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                return text.replace("时间：", "").replace("来源：", "").strip()
        return ""

    @staticmethod
    def _get_text(url: str) -> str:
        with httpx.Client(timeout=20, follow_redirects=True, headers=DEFAULT_HEADERS) as client:
            response = client.get(url)
            response.raise_for_status()
            response.encoding = response.encoding or "utf-8"
            return response.text
