import os
import uuid
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import shutil
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
)
from langchain_core.runnables import RunnableConfig
from rich.console import Console
from utils import print_message
from agent import agent


st.set_page_config(
    page_title="Cyber Hammer",
    page_icon=":robot:",
    layout="wide",
)
st.markdown("## Cyber Hammer")


load_dotenv()

SANDBOX_DIR = "./sandbox"

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())


config: RunnableConfig = {"configurable": {"thread_id": st.session_state["thread_id"]}}
print(f"Thread ID: {st.session_state['thread_id']}")


# create the agent with session state
if "agent" not in st.session_state:
    st.session_state["agent"] = agent


if "printed_messages" not in st.session_state:
    st.session_state["printed_messages"] = 0


# ------------------------------------------
# Sidebar
with st.sidebar:
    st.header("Cyber Hammer")

    # st.subheader("Chatbot Configuration")
    st.image("icon/cyberhammer.webp", width="stretch")
    # New: Sandbox Files Section (Alternative with selectbox)
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
            f.relative_to(sandbox_dir) for f in sandbox_dir.rglob("*") if f.is_file()
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
                        AIMessage(content=f"### File: `{selected_file}`\n\n" + content)
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
        st.session_state["agent"] = agent
        st.rerun()

    st.caption("Session ID: `" + st.session_state["thread_id"][:16] + "...`")

# show the history messages
for msg in st.session_state["messages"]:
    with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
        st.markdown(msg.content)


if prompt := st.chat_input("Ask me anything about a topic..."):
    human_msg = HumanMessage(content=prompt)
    st.session_state["messages"].append(human_msg)
    console = Console()
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_container = st.empty()
            full_response = ""

            try:
                for step in st.session_state["agent"].stream(
                    {"messages": [human_msg]},
                    config=config,
                    stream_mode="values",
                ):
                    messages: list[BaseMessage] = step["messages"]

                    for msg in messages[st.session_state["printed_messages"] :]:
                        msg: BaseMessage

                        print_message(console=console, msg=msg)

                        if isinstance(msg, HumanMessage):
                            continue
                        elif isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    tool_name = tool_call["name"]
                                    tool_args = tool_call["args"]
                                    full_response += f"\n\n**Using Tool:** `{tool_name}` with `{tool_args}`"
                            if msg.content:
                                full_response += "\n\n" + msg.content

                        else:
                            full_response += "\n\n" + "No relevant results found.\n"

                    st.session_state["printed_messages"] = len(messages)
                    response_container.markdown(full_response)

                ai_msg = AIMessage(content=full_response)
                st.session_state["messages"].append(ai_msg)

            except Exception as e:
                st.error(f"Error: {str(e)}")
