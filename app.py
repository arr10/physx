"""HomeFit — entry point: the shared header, then whichever page is selected.

Run:  streamlit run app.py
Key:  set OPENAI_API_KEY in your environment, .streamlit/secrets.toml, or paste it in Settings.
"""
import streamlit as st

from core import logo_mark, render_header
from i18n import t

st.set_page_config(page_title="HomeFit", page_icon=logo_mark(), layout="wide")

PAGES = [
    st.Page("pages/0_Welcome.py", title=t("nav_welcome"), url_path="welcome", default=True),
    st.Page("pages/1_Start.py", title=t("nav_start"), url_path="start"),
    st.Page("pages/1_Chat.py", title=t("nav_chat"), url_path="chat"),
    st.Page("pages/2_Your_plan.py", title=t("nav_plan"), url_path="plan"),
]

# position="hidden" drops Streamlit's sidebar menu — the header buttons navigate instead.
navigation = st.navigation(PAGES, position="hidden")
render_header(PAGES, navigation)
navigation.run()
