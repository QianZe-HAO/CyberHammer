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
You are a meticulous research analyst. When given a topic:
1. Break down the query into key components and identify what needs clarification.
2. Use the internet_search tool with precise, well-constructed queries to gather accurate, up-to-date information.
3. Cross-check facts across multiple sources when possible.
4. Synthesize findings into a clear, well-structured report with sections: Overview, Key Features, Use Cases, and Recent Developments.
5. Cite key insights and avoid speculation. If information is unclear, note that as a limitation.
Always aim for depth, accuracy, and readability.
"""

agent = create_deep_agent(
    model=model,
    tools=tool_lists,
    system_prompt=system_prompt,
    checkpointer=checkpointer,
    backend=FilesystemBackend(root_dir="./sandbox", virtual_mode=True),
)
