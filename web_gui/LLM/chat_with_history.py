from langchain.memory import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st


def lang_history(model, api_key, system_message):
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

    return chain_with_message_history