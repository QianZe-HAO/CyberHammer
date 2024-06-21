import streamlit as st
import config.proxy as proxy
import LLM.chat_with_history as chat_with_history


# using v2rayn
proxy.set_proxy()


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
    "[Get an Gemini API key](https://aistudio.google.com/)")
st.sidebar.markdown(
    "[View Source Code](https://github.com/QianZe-HAO/CyberHammer)")

# Check if the API key is provided
if not api_key:
    st.sidebar.error("Please enter your Gemini API Key.")
    st.stop()
else:
    # Store the API key in session state
    st.session_state.api_key = api_key


system_message = st.sidebar.text_area(
    "System Message", value="You are a helpful assistant. Answer all questions to the best of your ability.")

# ----------------------------------------------------------------
# Create a chain with message history
chain_with_message_history = chat_with_history.lang_history(
    model,
    api_key,
    system_message)
# ----------------------------------------------------------------

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
