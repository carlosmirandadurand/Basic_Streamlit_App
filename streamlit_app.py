import streamlit as st

with st.sidebar:
    # openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    # "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    bi_analyst_pwd = st.text_input("BI Analyst Password", key="bi_analyst_pwd", type="password")
    "[View the source code](https://github.com/carlosmirandadurand/Basic_Streamlit_App)"

st.title("Basic Streamlit Apps")
st.caption("Click on an app to continue...")

