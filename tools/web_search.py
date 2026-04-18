from langchain_community.utilities import SearxSearchWrapper
from dotenv import load_dotenv
import os

load_dotenv()

SEARXNG_HOST = os.getenv("SEARXNG_HOST", "http://localhost")
SEARXNG_PORT = os.getenv("SEARXNG_PORT", "8080")

searx_url = f"{SEARXNG_HOST}:{SEARXNG_PORT}"
search_wrapper = SearxSearchWrapper(searx_host=searx_url)


def internet_search(
    query: str,
    num_results: int = 5,
) -> list:
    """
    Performs a web search using a self-hosted or remote SearxNG instance and returns
    structured results.

    Returns a list of dictionaries with keys: 'title', 'snippet', 'link', 'engines', 'category'.

    Args:
        query (str): The search query to execute.
        num_results (int): Number of top results to return. Default is 5.

    Returns:
        list: List of dictionaries containing structured search results.
              Example:
              [
                {
                  "title": "Python Async",
                  "snippet": "Learn async programming...",
                  "link": "https://example.com",
                  "engines": ["google"],
                  "category": "general"
                }
              ]
    """
    return search_wrapper.results(query=query, num_results=num_results)
