import streamlit as st
import pandas as pd
import openai

# st.write("""
# # My first app
# Hello *world!*
# """)
#
# df = pd.read_csv("my_data.csv")
# st.line_chart(df)

# Demo code by Streamlit: https://github.com/streamlit/llm-examples/tree/main
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/carlosmirandadurand/Basic_Streamlit_App)"

st.title("💬 Basic Streamlit App")
st.caption("🚀 Interact with the OpenAI ChatGPT API")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    openai.api_key = openai_api_key
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    msg = response.choices[0].message
    st.session_state.messages.append(msg)
    st.chat_message("assistant").write(msg.content)
    