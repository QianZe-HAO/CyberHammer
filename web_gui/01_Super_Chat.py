import config.proxy as proxy
from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
# runnable config
from langchain_core.runnables import RunnableConfig

# gemini model
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st


from langchain_community.utilities import SerpAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import Tool


# human message
# from langchain_core.messages import HumanMessage, SystemMessage


from langchain.chains.llm import LLMChain
from langchain.agents import StructuredChatAgent


# ----------------------------------------------------------------
# using v2rayn
proxy.set_proxy()
# ----------------------------------------------------------------


# ----------------------------------------------------------------
# show the chat interface and information part
st.set_page_config(page_title="Cyber Hammer", page_icon="💬")
st.title("💬 Cyber Hammer")
st.caption("🔍 Chat with Search Engine, Conversation Context and AI Agent")
st.markdown("This is Cyber Hammer's most advanced conversation system. Based on Langchain Agent, it can use a search engine and record conversations. It can also be used as a reference for subsequent conversations.")
# ----------------------------------------------------------------


# ----------------------------------------------------------------
# create history memory and reset chat history
msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=msgs, return_messages=True, memory_key="chat_history", output_key="output"
)
if len(msgs.messages) == 0 or st.sidebar.button("Reset chat history"):
    msgs.clear()
    msgs.add_ai_message("How can I help you?")
    st.session_state.steps = {}
# ----------------------------------------------------------------


# ----------------------------------------------------------------
# AI model selection
st.session_state.setdefault('gemini_api_key', None)
model = st.sidebar.radio("Select LLM Model", [
                         "gemini-1.5-flash", "gemini-1.5-pro"])

# Configure API key
gemini_api_key = st.sidebar.text_input(
    "Gemini API Key:", value=st.session_state.gemini_api_key)

# Check if the API key is provided
if not gemini_api_key:
    st.sidebar.error("Please enter your Gemini API Key.")
    st.sidebar.markdown(
        "[Get an Gemini API key](https://aistudio.google.com/)")
    st.stop()
else:
    # Store the API key in session state
    st.session_state.gemini_api_key = gemini_api_key
# ----------------------------------------------------------------


# ----------------------------------------------------------------
# Search Engine selection
st.session_state.setdefault('serp_api_key', None)
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
prefix = system_message
suffix = ""
llm_prompt = StructuredChatAgent.create_prompt(
    prefix=prefix,
    tools=tools,
    suffix=suffix,
    input_variables=["input", "chat_history", "agent_scratchpad"],
)
# ----------------------------------------------------------------


avatars = {"human": "user", "ai": "assistant"}
for idx, msg in enumerate(msgs.messages):
    with st.chat_message(avatars[msg.type]):
        # Render intermediate steps if any were saved
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)

if prompt := st.chat_input(placeholder="Enter your Query:"):
    st.chat_message("user").write(prompt)

    if not gemini_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash",
                                 google_api_key=gemini_api_key)

    tools = tools

    llm_chain = LLMChain(llm=llm, prompt=llm_prompt)
    agent = StructuredChatAgent(llm_chain=llm_chain, verbose=True, tools=tools)
    executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        verbose=True,
        memory=memory,
        tools=tools,
        return_intermediate_steps=True,
        handle_parsing_errors=True
    )

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(
            st.container(), expand_new_thoughts=False)
        cfg = RunnableConfig()
        cfg["callbacks"] = [st_cb]
        # response = executor.invoke(
        #     [SystemMessage(system_message), HumanMessage(prompt)],
        #     cfg)
        response = executor.invoke(
            prompt,
            cfg)
        st.write(response["output"])
        st.session_state.steps[str(
            len(msgs.messages) - 1)] = response["intermediate_steps"]
