from langchain_community.utilities import SearxSearchWrapper
from dotenv import load_dotenv
import os

load_dotenv()

SEARXNG_HOST = os.getenv("SEARXNG_HOST", "http://localhost")
SEARXNG_PORT = os.getenv("SEARXNG_PORT", "8080")

searx_url = f"{SEARXNG_HOST}:{SEARXNG_PORT}"
search_wrapper = SearxSearchWrapper(searx_host=searx_url)


# def internet_search(
#     query: str,
# ) -> str:
#     """
#     Performs a web search using a self-hosted or remote SearxNG instance and returns
#     a concatenated string of the top search results.

#     This function leverages the SearxSearchWrapper from LangChain to send a query
#     to a SearxNG search engine, which aggregates results from multiple sources
#     while preserving user privacy. The results are parsed and combined into a
#     single string containing titles, snippets, and URLs of the most relevant pages.

#     Args:
#         query (str): The search query to be executed. Must be a non-empty string.
#                      Special characters and natural language are supported.

#     Returns:
#         str: A string containing aggregated information from the top search results.
#              Each result is typically formatted as:
#              "Title - Snippet... [URL]"
#              If no results are found, an empty string is returned.

#              Example return value:
#              "Python Async Programming - Learn how to use async/await in Python...
#              https://example.com/python-async |
#              Asyncio Documentation - Official Python documentation...
#              https://docs.python.org/3/library/asyncio.html"

#     Note:
#         - The quality and availability of results depend on the configured SearxNG instance.
#         - Ensure that the SearxNG server is running and accessible at the specified host and port.
#         - Network latency, query complexity, and SearxNG configuration may affect response time.
#     """
#     return search_wrapper.run(query=query)


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
