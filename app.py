"""HomeFit — entry point: the shared header, then whichever page is selected.

Run:  streamlit run app.py
Key:  set OPENAI_API_KEY in your environment, .streamlit/secrets.toml, or paste it in Settings.
"""
import streamlit as st

from core import logo_mark, render_header

st.set_page_config(page_title="HomeFit", page_icon=logo_mark(), layout="wide")

PAGES = [
    st.Page("pages/0_Welcome.py", title="Welcome", url_path="welcome", default=True),
    st.Page("pages/1_Start.py", title="Start", url_path="start"),
    st.Page("pages/1_Chat.py", title="Chat", url_path="chat"),
    st.Page("pages/2_Your_plan.py", title="Your plan", url_path="plan"),
]

# position="hidden" drops Streamlit's sidebar menu — the header buttons navigate instead.
navigation = st.navigation(PAGES, position="hidden")
render_header(PAGES, navigation)
navigation.run()
