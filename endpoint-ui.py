import streamlit as st
from pages import markdown_convert_page
from pages import chat_agent_page


pg = st.navigation(
    [
        st.Page(chat_agent_page, title="Deep Agent Chat"),







        st.Page(markdown_convert_page, title="Convert Files to Markdown"),
    ]
)

pg.run()
