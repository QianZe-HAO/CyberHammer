import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from tools import __all__ as tool_lists
from checkpointers import get_checkpointer

load_dotenv()


# -----------------------------------------------------
USE_POSTGRES = os.getenv("USE_POSTGRES", "true").lower() == "true"
checkpointer = get_checkpointer(use_postgres=USE_POSTGRES)

# -----------------------------------------------------
# Define model configuration from environment
MAIN_LLM_BASE_URL = os.getenv("MAIN_LLM_BASE_URL")
MAIN_LLM_API_KEY = os.getenv("MAIN_LLM_API_KEY")
MAIN_LLM_MODEL_NAME = os.getenv("MAIN_LLM_MODEL_NAME")

if not all([MAIN_LLM_BASE_URL, MAIN_LLM_API_KEY, MAIN_LLM_MODEL_NAME]):
    raise EnvironmentError(
        "Missing one or more required environment variables: MAIN_LLM_BASE_URL, MAIN_LLM_API_KEY, MAIN_LLM_MODEL_NAME"
    )

# Initialize the model and agent
model = ChatOpenAI(
    base_url=MAIN_LLM_BASE_URL,
    api_key=MAIN_LLM_API_KEY,
    model=MAIN_LLM_MODEL_NAME,
)


system_prompt = """
You are a meticulous research analyst with strong awareness of temporal context. The current date is: {current_time}.

When given a topic:
1. Break down the query into key components and identify what needs clarification.
2. Use the internet_search tool with precise, well-constructed queries. Include time filters when relevant (e.g., "2023", "since 2024", "latest") to ensure up-to-date results.
3. Always assess the recency and relevance of information. Prefer sources from the past 1–2 years unless historical context is needed.
4. Clearly distinguish between:
   - Established facts
   - Recent developments (highlight their timing)
   - Emerging trends vs. short-lived fads
5. In your report, include a note on data freshness: mention the time range of sources used.
6. Synthesize findings into a clear, well-structured report with sections: Overview, Key Features, Use Cases, and Recent Developments (with approximate dates).
7. Cite key insights and avoid speculation. If information is unclear or outdated, note that as a limitation.

Always aim for depth, accuracy, readability, and temporal awareness.
""".format(current_time=__import__('datetime').datetime.now().strftime("%Y-%m-%d"))

agent = create_deep_agent(
    model=model,
    tools=tool_lists,
    system_prompt=system_prompt,
    checkpointer=checkpointer,
    backend=FilesystemBackend(root_dir="./sandbox", virtual_mode=True),
)
