from langchain.memory import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
import os

# using v2rayn
os.environ["HTTP_PROXY"] = "http://127.0.0.1:10809"
os.environ["HTTP_PROXYS"] = "http://127.0.0.1:10809"

# model = "gemini-1.5-flash"

st.session_state.setdefault('api_key', None)
st.title("💬 Cyber Hammer")
st.caption("📕 Chat with Conversation Context")

# AI model
model = st.sidebar.radio("Select LLM Model", [
                         "gemini-1.5-flash", "gemini-1.5-pro"])

# Configure API key
api_key = st.sidebar.text_input(
    "Gemini API Key:", value=st.session_state.api_key)
st.sidebar.markdown(
    "[Get an Gemini API key](https://platform.openai.com/account/api-keys)")
st.sidebar.markdown(
    "[View Source Code](https://github.com/QianZe-HAO/CyberHammer)")

# Check if the API key is provided
if not api_key:
    st.sidebar.error("Please enter your Gemini API Key.")
    st.stop()
else:
    # Store the API key in session state
    st.session_state.api_key = api_key

# system_message = st.sidebar.text_input("Input System Message:", "You are a helpful assistant. Answer all questions to the best of your ability. Answer me in Chinese.")

system_message = st.sidebar.text_area(
    "System Message", value="You are a helpful assistant. Answer all questions to the best of your ability.")


chat = ChatGoogleGenerativeAI(model=model, google_api_key=api_key)

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessage(system_message),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)

chain = prompt | chat

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = ChatMessageHistory()

chain_with_message_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: st.session_state["chat_history"],
    input_messages_key="input",
    history_messages_key="chat_history",
)

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

prompt = st.chat_input("Enter your Query:")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    try:
        response = chain_with_message_history.invoke(
            {"input": prompt},
            {"configurable": {"session_id": "abc23"}},
        )

        if response.content:
            msg = response.content
            st.session_state.messages.append(
                {"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
        else:
            st.write("No output from Gemini.")

    except Exception as e:
        st.write(f"An error occurred: {str(e)}")
