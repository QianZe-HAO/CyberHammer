import asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    CrawlResult,
)
from typing import cast
from crawl4ai.models import MarkdownGenerationResult


def crawl_url(url: str, headless: bool = True, verbose: bool = False) -> str:
    """
    Synchronously crawl a given URL and return the content as Markdown string.

    Args:
        url (str): The URL to crawl.
        headless (bool): Whether to run browser in headless mode. Default is True.
        verbose (bool): Whether to enable verbose logging. Default is False.

    Returns:
        str: The crawled content in Markdown format, or error message.
    """

    async def _async_crawl():
        browser_config = BrowserConfig(
            headless=headless,
            verbose=verbose,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            crawler_config = CrawlerRunConfig(
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=PruningContentFilter()
                ),
            )
            try:
                result: CrawlResult = await crawler.arun(url=url, config=crawler_config)
                # return result.markdown.raw_markdown
                markdown_result = getattr(
                    result.markdown, "_markdown_result", None)
                if markdown_result is not None:
                    return cast(MarkdownGenerationResult, markdown_result).raw_markdown
                return result.markdown or ""  # fallback to string coercion
            except Exception as e:
                return f"Error: {str(e)}"

    return asyncio.run(_async_crawl())
