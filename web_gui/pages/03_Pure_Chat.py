import streamlit as st
import google.generativeai as genai
import json
import os
import config.proxy as proxy


# using v2rayn
proxy.set_proxy()

st.set_page_config(page_title="Cyber Hammer", page_icon="💬")

st.session_state.setdefault('api_key', None)
st.title("💬 Cyber Hammer")
st.caption("🚀 A powerful Chatbot powered by Zehao Qian")


# Configure API key
api_key = st.sidebar.text_input(
    "Gemini API Key:", value=st.session_state.api_key)

# Check if the API key is provided
if not api_key:
    st.sidebar.error("Please enter your Gemini API Key.")
    st.stop()
else:
    # Store the API key in session state
    st.session_state.api_key = api_key

genai.configure(api_key=api_key)


# st.write(st.session_state.api_key)
# Set up the model configuration options
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.9, 0.1)
top_p = st.sidebar.number_input("Top P", 0.0, 1.0, 1.0, 0.1)
top_k = st.sidebar.number_input("Top K", 1, 100, 1)
max_output_tokens = st.sidebar.number_input(
    "Max Output Tokens", 1, 10000, 2048)

# Set up the model
generation_config = {
    "temperature": temperature,
    "top_p": top_p,
    "top_k": top_k,
    "max_output_tokens": max_output_tokens,
}


safety_settings = "{}"
safety_settings = json.loads(safety_settings)

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


prompt = st.chat_input("Enter your Query:")
# Check if the query is provided
if not prompt:
    st.error("Please enter your query.")
    st.stop()

# --------------------------------------------------------------------------
gemini = genai.GenerativeModel(model_name="gemini-pro",
                               generation_config=generation_config,
                               safety_settings=safety_settings)


prompt_parts = [prompt]
# --------------------------------------------------------------------------
st.session_state.messages.append({"role": "user", "content": prompt})
st.chat_message("user").write(prompt)

try:
    response = gemini.generate_content(prompt_parts)
    # st.subheader("Gemini:")
    if response.text:
        # st.write(response.text)
        msg = response.text
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)
    else:
        st.write("No output from Gemini.")

    # st.session_state.messages.append({"role": "assistant", "content": msg})
    # st.chat_message("assistant").write(msg)

except Exception as e:
    st.write(f"An error occurred: {str(e)}")
