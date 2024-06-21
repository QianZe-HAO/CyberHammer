import streamlit as st
import config.proxy as proxy
# tools for search
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import Tool
# add context memory
from langgraph.checkpoint.sqlite import SqliteSaver
# gemini model
from langchain_google_genai import ChatGoogleGenerativeAI
# langgraph pre-built agent
from langgraph.prebuilt import create_react_agent
# human message
from langchain_core.messages import HumanMessage, SystemMessage
# ----------------------------------------------------------------
# using v2rayn
proxy.set_proxy()
# ----------------------------------------------------------------


st.session_state.setdefault('api_key', None)
st.session_state.setdefault('serp_api_key', None)

st.title("💬 Cyber Hammer")
st.caption("🔍 Chat with Search Engine")

# ----------------------------------------------------------------
# AI model selection
model = st.sidebar.radio("Select LLM Model", [
                         "gemini-1.5-flash", "gemini-1.5-pro"])

# Configure API key
api_key = st.sidebar.text_input(
    "Gemini API Key:", value=st.session_state.api_key)

# Check if the API key is provided
if not api_key:
    st.sidebar.error("Please enter your Gemini API Key.")
    st.sidebar.markdown(
        "[Get an Gemini API key](https://aistudio.google.com/)")
    st.stop()
else:
    # Store the API key in session state
    st.session_state.api_key = api_key
# ----------------------------------------------------------------


# ----------------------------------------------------------------
# Search Engine selection
search_selection = st.sidebar.radio("Select Search Tool", [
    "DuckDuckGo", "SerpAPI"])
if search_selection == "DuckDuckGo":
    search_tool = DuckDuckGoSearchResults(name="Search")
elif search_selection == "SerpAPI":
    serp_api_key = st.sidebar.text_input(
        "Serp API Key:", value=st.session_state.serp_api_key)

    if not serp_api_key:
        st.sidebar.error("Please enter your SerpAPI Key.")
        st.sidebar.markdown('[Get a SerpAPI key](https://serpapi.com/)')
        st.stop()
    else:
        st.session_state.serp_api_key = serp_api_key
        search = SerpAPIWrapper(serpapi_api_key=st.session_state.serp_api_key)
        search_tool = Tool(
            name="serpapi",
            description="A tool that uses the SerpAPI to search the web.",
            func=search.run,
        )
tools = [search_tool]
# ----------------------------------------------------------------


# ----------------------------------------------------------------
# link to source code
st.sidebar.markdown(
    "[View Source Code](https://github.com/QianZe-HAO/CyberHammer)")
# ----------------------------------------------------------------


# ----------------------------------------------------------------
# System message
system_message = st.sidebar.text_area(
    "System Message", value="You are a helpful assistant. Answer all questions to the best of your ability.")
# ----------------------------------------------------------------


# ----------------------------------------------------------------
# Create a chain
if "chat_history_config" not in st.session_state:
    st.session_state["chat_history_config"] = {
        "configurable": {"thread_id": "abc123"}}


chat = ChatGoogleGenerativeAI(model=model,
                              google_api_key=api_key)

memory = SqliteSaver.from_conn_string(":memory:")
agent_executor = create_react_agent(chat, tools, checkpointer=memory)
config = st.session_state["chat_history_config"]
# ----------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

prompt = st.chat_input("Enter your Query:")


# ----------------------------------------------------------------
# Chat with Search Engine
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        response = agent_executor.invoke(
            {"messages": [SystemMessage(system_message), HumanMessage(prompt)]}, config=config
        )

        if response['messages'][-1].content:
            print(response)
            msg = response['messages'][-1].content
            st.session_state.messages.append(
                {"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
        else:
            st.write("No output from Gemini.")

    except Exception as e:
        st.write(f"An error occurred: {str(e)}")
# ----------------------------------------------------------------
