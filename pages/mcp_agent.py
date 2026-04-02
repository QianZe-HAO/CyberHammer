# pages/mcp_agent.py
import os
import uuid
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

import streamlit as st
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from rich.console import Console

# LangChain & MCP imports
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from checkpointers import get_checkpointer

# -----------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------
load_dotenv()

USE_POSTGRES = os.getenv("USE_POSTGRES", "true").lower() == "true"
checkpointer = get_checkpointer(use_postgres=USE_POSTGRES)

# Model configuration
MAIN_LLM_BASE_URL = os.getenv("MAIN_LLM_BASE_URL")
MAIN_LLM_API_KEY = os.getenv("MAIN_LLM_API_KEY")
MAIN_LLM_MODEL_NAME = os.getenv("MAIN_LLM_MODEL_NAME")


def load_mcp_config(config_path=".mcp.json"):
    """Load MCP server configuration from JSON file"""
    mcp_servers = {}

    # Try .mcp.json file first
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                mcp_servers = json.load(f)
            if not isinstance(mcp_servers, dict):
                mcp_servers = {}
            print(f"Loaded MCP config from {config_path}: {mcp_servers}")
        except json.JSONDecodeError as e:
            print(f"Error parsing {config_path}: {e}")
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass

    # Default server if no configuration provided
    if not mcp_servers:
        mcp_servers = {
            "mcp-manager": {
                "transport": "sse",
                "url": os.getenv("MCP_SERVER_1_URL", "http://localhost:8000/sse"),
            },
        }

    return mcp_servers


MCP_SERVERS = load_mcp_config()


# Default server if no configuration provided
if not MCP_SERVERS:
    MCP_SERVERS = {
        "mcp-manager": {
            "transport": "sse",
            "url": os.getenv("MCP_SERVER_1_URL", "http://localhost:8000/sse"),
        },
    }

# Validate required environment variables
if not all([MAIN_LLM_BASE_URL, MAIN_LLM_API_KEY, MAIN_LLM_MODEL_NAME]):
    raise EnvironmentError(
        "Missing one or more required environment variables: "
        "MAIN_LLM_BASE_URL, MAIN_LLM_API_KEY, MAIN_LLM_MODEL_NAME"
    )

# Initialize the model
model = ChatOpenAI(
    base_url=MAIN_LLM_BASE_URL,
    api_key=MAIN_LLM_API_KEY,
    model=MAIN_LLM_MODEL_NAME,
)


# -----------------------------------------------------
# MCP AGENT FACTORY
# -----------------------------------------------------
class MCPAgentFactory:
    """Factory class for creating and managing MCP agents"""

    @staticmethod
    async def create_agent():
        """Create MCP-based agent from multi-server MCP client"""
        client = MultiServerMCPClient(MCP_SERVERS)
        tools = await client.get_tools()

        system_prompt = """
        You are a cybersecurity analyst with MCP tool access.
        Current date: {}

        Use MCP tools to gather information and perform calculations.
        Always explain your tool usage clearly in the response.
        """.format(
            datetime.now().strftime("%Y-%m-%d")
        )

        agent = create_deep_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            checkpointer=checkpointer,
            backend=FilesystemBackend(root_dir="./sandbox", virtual_mode=True),
        )

        return agent


# Global cache for agent instance
_mcp_agent_instance = None


async def get_mcp_agent():
    """Get or create MCP agent instance"""
    global _mcp_agent_instance
    if _mcp_agent_instance is None:
        _mcp_agent_instance = await MCPAgentFactory.create_agent()
    return _mcp_agent_instance


# -----------------------------------------------------
# STREAMLIT PAGE
# -----------------------------------------------------
def mcp_agent_page():
    """Main Streamlit page for MCP Agent interface"""
    st.set_page_config(
        page_title="Cyber Hammer MCP Agent",
        layout="wide",
    )
    st.markdown("## Cyber Hammer MCP Agent")
    st.markdown("Using Model Context Protocol for multi-server tool access")

    SANDBOX_DIR = "./sandbox"

    # Sidebar: Server Status
    with st.sidebar:
        st.header("MCP Servers")

        for server_name, server_config in MCP_SERVERS.items():
            with st.expander(server_name, expanded=False):
                st.metric("Transport", server_config.get("transport", "unknown"))
                if server_config.get("url"):
                    st.text_input(
                        "URL",
                        value=server_config["url"],
                        disabled=True,
                        label_visibility="collapsed",
                    )

        st.divider()
        st.subheader("Configuration")
        show_server_status = st.checkbox("Show Server Status", value=False)

        if show_server_status:
            st.info("Server connections established on first tool call")

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid.uuid4())
    if "agent_initialized" not in st.session_state:
        st.session_state["agent_initialized"] = False

    config: RunnableConfig = {
        "configurable": {"thread_id": st.session_state["thread_id"]}
    }
    st.caption("Session ID: {}".format(st.session_state["thread_id"][:16]))

    # Initialize agent on first request
    if not st.session_state["agent_initialized"]:
        with st.spinner("Initializing MCP Agent..."):
            try:
                asyncio.run(get_mcp_agent())
                st.session_state["agent_initialized"] = True
                st.success("MCP Agent initialized")
            except Exception as e:
                st.error("Failed to initialize MCP Agent: {}".format(e))
                st.stop()

    # Show message history
    for msg in st.session_state["messages"]:
        with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
            st.markdown(msg.content)

    # Chat input
    if prompt := st.chat_input("Ask something"):
        human_msg = HumanMessage(content=prompt)
        st.session_state["messages"].append(human_msg)
        console = Console()

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_container = st.empty()
            full_response = ""
            tool_calls_used = []

            try:
                agent = asyncio.run(get_mcp_agent())
                ai_response = asyncio.run(
                    agent.ainvoke(
                        {"messages": [human_msg]},
                        config=config,
                    )
                )

                # Extract content from response
                ai_msg = ai_response["messages"][-1]
                if isinstance(ai_msg, AIMessage):
                    # Log tool calls
                    if ai_msg.tool_calls:
                        for tool_call in ai_msg.tool_calls:
                            tool_name = tool_call["name"]
                            tool_args = tool_call["args"]
                            full_response += (
                                "\n\n"
                                + "**Using MCP Tool:** `{}`\n`{}`".format(
                                    tool_name, json.dumps(tool_args, indent=2)
                                )
                            )
                            tool_calls_used.append(
                                {"name": tool_name, "args": tool_args}
                            )

                    # Add main response content
                    if ai_msg.content:
                        full_response += "\n\n" + str(ai_msg.content)
                    else:
                        full_response = "No response content available."

                # Display the response
                response_container.markdown(full_response, unsafe_allow_html=True)
                st.session_state["messages"].append(ai_msg)

            except Exception as e:
                st.error("Error: {}".format(str(e)))
                st.info("Make sure your MCP servers are running")
                st.exception(e)
