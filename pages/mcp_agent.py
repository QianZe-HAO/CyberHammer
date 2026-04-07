import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import shutil
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from datetime import datetime
import asyncio
import json

# LangChain & MCP imports
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from checkpointers import get_async_checkpointer

# -----------------------------------------------------
USE_POSTGRES = True
SANDBOX_DIR = "./sandbox"

# ... existing code ...


def _get_streamlit_loop():
    """Get Streamlit event loop (non-blocking)"""
    try:
        # 3.12+ compatible way
        loop = asyncio.get_running_loop()
        return loop
    except RuntimeError:
        # No running loop, create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


class AgentApp:
    """Streamlit MCP Agent Application"""

    def __init__(self):
        self.sandbox_dir = Path(SANDBOX_DIR)
        self.session_id = None
        self.agent = None
        self.config = None
        self.mcp_client = None
        self.tools = None
        self._initialized = False
        self._init_session()

    def _init_session(self):
        """Initialize session state"""
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        if "session_id" not in st.session_state:
            st.session_state["session_id"] = str(uuid.uuid4())
        self.session_id = st.session_state["session_id"]

    def ensure_agent_initialized(self):
        """Ensure agent is initialized (non-blocking)"""
        if not self._initialized:
            loop = _get_streamlit_loop()
            if loop.is_running():
                # Create task in existing loop
                loop.create_task(self._async_init_agent())
            else:
                # Run until completion
                loop.run_until_complete(self._async_init_agent())
            self._initialized = True

    async def _async_init_agent(self):
        """Asynchronous agent initialization"""
        if self.mcp_client is None:
            self.mcp_client = MultiServerMCPClient(
                connections={
                    "mcp-manager": {
                        "transport": "sse",
                        "url": "http://host.docker.internal:8000/sse",
                    },
                }
            )

        if self.tools is None:
            self.tools = await self.mcp_client.get_tools()

        system_prompt = f"""
        You are a cybersecurity analyst with MCP tool access.
        Current date: {datetime.now().strftime("%Y-%m-%d")}
        
        Use MCP tools to gather information and perform calculations.
        Always explain your tool usage clearly in the response.
        """

        model = ChatOpenAI(
            base_url=os.getenv("MAIN_LLM_BASE_URL"),
            api_key=os.getenv("MAIN_LLM_API_KEY"),
            model=os.getenv("MAIN_LLM_MODEL_NAME"),
        )

        checkpointer = await get_async_checkpointer(use_postgres=USE_POSTGRES)

        self.agent = create_deep_agent(
            model=model,
            tools=self.tools,
            system_prompt=system_prompt,
            checkpointer=checkpointer,
            backend=FilesystemBackend(root_dir=SANDBOX_DIR, virtual_mode=True),
        )
        self.config: RunnableConfig = {"configurable": {"thread_id": self.session_id}}

    def handle_file_upload(self):
        """Handle file upload"""
        uploaded_file = st.file_uploader(
            "Choose a file to upload",
            type=["md"],
            accept_multiple_files=False,
            label_visibility="collapsed",
            width="stretch",
        )

        if uploaded_file is not None:
            upload_dest = self.sandbox_dir / uploaded_file.name
            self.sandbox_dir.mkdir(exist_ok=True)

            try:
                with open(upload_dest, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.toast(f"Uploaded: {uploaded_file.name}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save file: {e}")

    def show_sandbox_files(self):
        """Show sandbox files"""
        st.subheader("Sandbox Files")

        files = [
            f.relative_to(self.sandbox_dir)
            for f in self.sandbox_dir.rglob("*")
            if f.is_file()
        ]

        if files:
            selected_file = st.selectbox(
                "Choose a file to view",
                options=files,
                key="selected_sandbox_file",
                label_visibility="collapsed",
                width="stretch",
            )
            file_path = self.sandbox_dir / selected_file

            if st.button(
                "Show File",
                key="show_file_btn",
                width="stretch",
            ):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    st.session_state["messages"].append(
                        AIMessage(content=f"### File: {selected_file}\n\n" + content)
                    )
                except Exception as e:
                    st.error(f"Could not read file: {e}")

            with open(file_path, "rb") as f:
                st.download_button(
                    label="Download File",
                    data=f,
                    file_name=str(selected_file),
                    mime=(
                        "text/markdown"
                        if selected_file.suffix == ".md"
                        else "text/plain"
                    ),
                    use_container_width=True,
                    key="download_file_btn",
                    width="stretch",
                )

            if st.button(
                "Clear Sandbox",
                key="clear_sandbox_btn",
                width="stretch",
            ):
                try:
                    if self.sandbox_dir.exists():
                        shutil.rmtree(self.sandbox_dir)
                    self.sandbox_dir.mkdir(exist_ok=True)
                    st.success("Sandbox cleared!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing sandbox: {e}")
        else:
            st.caption("No files in sandbox. Upload a file to begin.")

    def handle_user_input(self):
        """Handle user input and generate response"""
        prompt = st.chat_input("Ask me anything about a topic...")

        if not prompt:
            return

        human_msg = HumanMessage(content=prompt)
        st.session_state["messages"].append(human_msg)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Ensure agent is initialized
            if self.agent is None:
                with st.spinner("Initializing agent..."):
                    self.ensure_agent_initialized()

                if self.agent is None:
                    st.error("Failed to initialize agent")
                    return

            self._run_agent_response(human_msg)

    def _run_agent_response(self, human_msg):
        """Run agent and display streaming response"""
        if self.agent is None:
            st.error("Agent not initialized")
            return

        response_container = st.empty()
        full_response = ""
        printed_count = 0

        async def run_stream():
            nonlocal full_response, printed_count
            try:
                async for step in self.agent.astream(
                    {"messages": [human_msg]},
                    config=self.config,
                    stream_mode="values",
                ):
                    messages = step.get("messages", [])
                    new_count = len(messages)

                    for msg in messages[printed_count:]:
                        if isinstance(msg, HumanMessage):
                            continue
                        elif isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    full_response += f"\n\n**Using MCP Tool:** {tool_call['name']}\n```json {json.dumps(tool_call['args'])}```"
                            if msg.content:
                                full_response += "\n" + msg.content

                        elif isinstance(msg, ToolMessage):
                            content_str = str(msg.content).strip()
                            preview = content_str[:50]
                            with st.expander(f"MCP Tool: {msg.name} ({preview}...)"):
                                try:
                                    st.json(json.loads(content_str))
                                except:
                                    st.markdown(content_str)

                    printed_count = new_count
                    response_container.markdown(full_response)
            except Exception as e:
                response_container.markdown(f"**Error:** {str(e)}")

        # Run asynchronous code in Streamlit
        loop = _get_streamlit_loop()
        if loop.is_running():
            loop.create_task(run_stream())
        else:
            loop.run_until_complete(run_stream())

        ai_msg = AIMessage(content=full_response)
        st.session_state["messages"].append(ai_msg)


# Main Page
def mcp_agent_page():
    st.set_page_config(page_title="Cyber Hammer", layout="wide")
    st.markdown("## Cyber Hammer")

    load_dotenv()
    os.makedirs(SANDBOX_DIR, exist_ok=True)

    # Initialize application instance
    app = AgentApp()

    # Sidebar
    with st.sidebar:
        st.header("Cyber Hammer")
        try:
            st.image("icon/cyberhammer.webp", width=300)
        except:
            st.header("Cyber Hammer")

        st.subheader("MCP Tools")
        st.success("Connected to mcp-manager")

        # File upload
        app.handle_file_upload()

        # Sandbox file management
        app.show_sandbox_files()

        st.divider()

        if st.button(
            "Start a New Session",
            width="stretch",
        ):
            st.session_state["messages"] = []
            st.session_state["session_id"] = str(uuid.uuid4())
            app = AgentApp()  # Reinitialize
            st.rerun()

        st.caption(f"Session: {st.session_state['session_id'][:16]}...")

    # Display historical messages
    for msg in st.session_state["messages"]:
        with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
            st.markdown(msg.content)

    # Handle user input
    app.handle_user_input()
