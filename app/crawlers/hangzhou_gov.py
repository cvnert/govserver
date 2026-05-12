from app.crawlers.generic_gov import (
    DATE_SELECTORS,
    MAIN_CONTENT_SELECTORS,
    SOURCE_SELECTORS,
    TITLE_SELECTORS,
    GenericGovCrawler,
)


class HangzhouGovCrawler(GenericGovCrawler):
    title_selectors = [
        "meta[name='ArticleTitle']",
        "meta[name='title']",
        ".xxgk_title",
        ".article-title",
        ".title",
        "h1",
        *TITLE_SELECTORS,
    ]
    date_selectors = [
        "meta[name='PubDate']",
        "meta[name='publishdate']",
        ".xxgk_info",
        ".article-info",
        ".info",
        *DATE_SELECTORS,
    ]
    source_selectors = [
        "meta[name='ContentSource']",
        "meta[name='source']",
        ".xxgk_info",
        ".article-info",
        ".info",
        *SOURCE_SELECTORS,
    ]
    main_content_selectors = [
        "#zoom",
        ".TRS_Editor",
        ".xxgk_content",
        ".article-content",
        ".contMain",
        ".content",
        *MAIN_CONTENT_SELECTORS,
    ]
