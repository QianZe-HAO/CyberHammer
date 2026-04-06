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
from rich.console import Console
from datetime import datetime
import asyncio

from openai import OpenAI

# LangChain & MCP imports
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
import json
from checkpointers import get_async_checkpointer


# -----------------------------------------------------
USE_POSTGRES = False


def mcp_agent_page():

    st.set_page_config(
        page_title="Cyber Hammer",
        layout="wide",
    )
    st.markdown("## Cyber Hammer")

    load_dotenv()

    SANDBOX_DIR = "./sandbox"

    # MCP Configuration
    MAIN_LLM_BASE_URL = os.getenv("MAIN_LLM_BASE_URL")
    MAIN_LLM_API_KEY = os.getenv("MAIN_LLM_API_KEY")
    MAIN_LLM_MODEL_NAME = os.getenv("MAIN_LLM_MODEL_NAME")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "thread_id" not in st.session_state:
        st.session_state["thread_id"] = str(uuid.uuid4())
    if "printed_messages" not in st.session_state:
        st.session_state["printed_messages"] = 0
    if "mcp_client" not in st.session_state:
        st.session_state["mcp_client"] = MultiServerMCPClient(
            connections={
                "mcp-manager": {
                    "transport": "sse",
                    "url": "http://host.docker.internal:8000/sse",
                },
            }
        )

    config: RunnableConfig = {
        "configurable": {"thread_id": st.session_state["thread_id"]}
    }
    print(f"Thread ID: {st.session_state['thread_id']}")

    # ------------------------------------------
    # Sidebar
    with st.sidebar:
        st.header("Cyber Hammer")
        st.image("icon/cyberhammer.webp", width="stretch")

        # MCP Tools Status
        st.subheader("MCP Tools")
        st.success("MCP Tools: Connected")

        # Sandbox Files Section
        st.subheader("Sandbox Files")
        sandbox_dir = SANDBOX_DIR
        os.makedirs(sandbox_dir, exist_ok=True)
        sandbox_dir = Path(SANDBOX_DIR)

        uploaded_file = st.file_uploader(
            "Choose a file to upload",
            type=["md"],
            accept_multiple_files=False,
            label_visibility="visible",
        )

        if "uploaded_file_name" not in st.session_state:
            st.session_state["uploaded_file_name"] = None

        if uploaded_file is not None:
            if st.session_state["uploaded_file_name"] != uploaded_file.name:
                upload_dest = sandbox_dir / uploaded_file.name
                try:
                    with open(upload_dest, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.toast(f"Uploaded: `{uploaded_file.name}`")
                    st.session_state["uploaded_file_name"] = uploaded_file.name
                    st.rerun()
                except Exception as e:
                    st.toast(f"Failed to save file: {e}")
            else:
                st.toast(f"`{uploaded_file.name}` has already been uploaded.")

        if os.path.exists(sandbox_dir):
            files = [
                f.relative_to(sandbox_dir)
                for f in sandbox_dir.rglob("*")
                if f.is_file()
            ]

            if files:
                selected_file = st.selectbox(
                    "Choose a file to view",
                    options=files,
                    key="selected_sandbox_file",
                    width="stretch",
                )
                file_path = sandbox_dir / selected_file

                if st.button("Show File", key="show_file_btn", width="stretch"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        st.session_state["messages"].append(
                            AIMessage(
                                content=f"### File: `{selected_file}`\n\n" + content
                            )
                        )
                    except Exception as e:
                        st.error(f"Could not read file: {e}")

                with open(file_path, "rb") as f:
                    st.download_button(
                        label="Download Selected File",
                        data=f,
                        file_name=str(selected_file),
                        mime=(
                            "text/markdown"
                            if selected_file.suffix == ".md"
                            else "text/plain"
                        ),
                        key="download_file_btn",
                        use_container_width=True,
                    )

                if st.button("Clear Sandbox", width="stretch"):
                    sandbox_dir = Path(SANDBOX_DIR)
                    try:
                        if sandbox_dir.exists():
                            shutil.rmtree(sandbox_dir)
                        sandbox_dir.mkdir(exist_ok=True)
                        st.success("Sandbox cleared successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error clearing sandbox: {e}")
            else:
                st.caption("No files in sandbox.")
        else:
            st.caption("Sandbox directory not found.")

        st.divider()

        if st.button("Start a New Session", width="stretch"):
            st.session_state["messages"] = []
            st.session_state["printed_messages"] = 0
            st.session_state["thread_id"] = str(uuid.uuid4())
            st.rerun()

        st.caption("Session ID: `" + st.session_state["thread_id"][:16] + "...`")

    # show the history messages
    for msg in st.session_state["messages"]:
        with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
            st.markdown(msg.content)


    if prompt := st.chat_input(
        "Ask me anything about a topic...",
        accept_audio=True,
        audio_sample_rate=16000,
    ):
        if prompt.text:
            prompt = prompt.text
        elif prompt.audio:
            prompt_audio_name = prompt.audio.read()
            asr_client = OpenAI(
                api_key=os.getenv("ASR_MODEL_API_KEY"),
                base_url=os.getenv(
                    "ASR_MODEL_BASE_URL",
                ),
            )
            prompt = asr_client.audio.transcriptions.create(
                file=prompt_audio_name,
                model=os.getenv("ASR_MODEL_NAME"),
            ).text
        else:
            st.stop()

        human_msg = HumanMessage(content=prompt)
        st.session_state["messages"].append(human_msg)
        console = Console()
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking with MCP tools..."):
                response_container = st.empty()
                full_response = ""

                try:
                    # 初始化 agent（避免每次消息都创建）
                    if "agent" not in st.session_state:

                        async def init_agent():
                            mcp_client = st.session_state["mcp_client"]
                            tools = await mcp_client.get_tools()

                            system_prompt = f"""
                            You are a cybersecurity analyst with MCP tool access.
                            Current date: {datetime.now().strftime("%Y-%m-%d")}

                            Use MCP tools to gather information and perform calculations.
                            Always explain your tool usage clearly in the response.
                            """

                            model = ChatOpenAI(
                                base_url=MAIN_LLM_BASE_URL,
                                api_key=MAIN_LLM_API_KEY,
                                model=MAIN_LLM_MODEL_NAME,
                            )

                            checkpointer = await get_async_checkpointer(
                                use_postgres=USE_POSTGRES
                            )

                            agent = create_deep_agent(
                                model=model,
                                tools=tools,
                                system_prompt=system_prompt,
                                checkpointer=checkpointer,
                                backend=FilesystemBackend(
                                    root_dir="./sandbox", virtual_mode=True
                                ),
                            )
                            return agent

                        import asyncio

                        asyncio.run(init_agent())
                        st.session_state["agent"] = asyncio.run(init_agent())

                    # 运行 agent（不需要 asyncio.run）
                    st.session_state["agent"] = st.session_state.get("agent")
                    if not st.session_state["agent"]:
                        st.error("Agent 未正确初始化")
                        st.stop()

                    async def run_agent_stream():
                        nonlocal full_response
                        async for step in st.session_state["agent"].astream(
                            {"messages": [human_msg]},
                            config=config,
                            stream_mode="values",
                        ):
                            messages = step["messages"]

                            for msg in messages[st.session_state["printed_messages"] :]:
                                if isinstance(msg, HumanMessage):
                                    continue
                                elif isinstance(msg, AIMessage):
                                    if msg.tool_calls:
                                        for tool_call in msg.tool_calls:
                                            tool_name = tool_call["name"]
                                            tool_args = tool_call["args"]
                                            full_response += f"\n\n**Using MCP Tool:** `{tool_name}` with `{tool_args}`"
                                    if msg.content:
                                        full_response += "\n\n" + msg.content

                                elif isinstance(msg, ToolMessage):
                                    msg_content = msg.content
                                    if msg_content:
                                        content_str = str(msg_content).strip()
                                        try:
                                            parsed_json = json.loads(content_str)
                                            is_json = True
                                        except json.JSONDecodeError:
                                            is_json = False

                                        preview = (
                                            content_str[:50].replace("\n", " ").strip()
                                        )
                                        with st.expander(
                                            f"MCP Tool {msg.name} Response ({preview}...)"
                                        ):
                                            if is_json:
                                                st.json(parsed_json)
                                            else:
                                                st.markdown(f"{content_str}")

                                st.session_state["printed_messages"] = len(messages)
                                response_container.markdown(full_response)

                            await asyncio.sleep(0.01)

                    # 修复: 使用 asyncio.run() 仅用于单次调用
                    import asyncio

                    asyncio.run(run_agent_stream())

                    ai_msg = AIMessage(content=full_response)
                    st.session_state["messages"].append(ai_msg)

                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    import traceback

                    st.code(traceback.format_exc())



