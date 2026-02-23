import os
from dotenv import load_dotenv
from tavily import TavilyClient

# Load environment variables
load_dotenv()

# Check if TAVILY_API_KEY exists
if not os.environ.get("TAVILY_API_KEY"):
    raise ValueError("TAVILY_API_KEY is missing. Please set it in your .env file.")

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    query: str,
    max_results: int = 5,
):
    """Run a web search with improved query understanding"""
    return tavily_client.search(
        query,
        max_results=max_results,
        search_depth="ultra-fast",
        include_images=False,
    )


def crawl_url(
    urls: list[str] | str,
    format: str = "markdown",
    extract_depth: str = "basic",
) -> dict:
    """
    Extract content from one or more URLs using Tavily's extraction API.

    Args:
        urls: A single URL or list of URLs to extract content from.
        format: Output format - 'markdown' (default) or 'text'.
        extract_depth: How deeply to extract - 'basic' or 'advanced' (default).
        max_retries: Number of retry attempts on failure (not directly used by Tavily client, but can be extended).

    Returns:
        Dictionary containing extracted 'results' and 'failed_results'.
    """
    return tavily_client.extract(
        urls=urls,
        include_images=False,
        format=format,
        extract_depth=extract_depth,
    )
