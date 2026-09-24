"""HomeFit — landing page: explains the concept before the intake form."""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from i18n import t  # noqa: E402

st.write(t("welcome_intro"))

st.subheader(t("welcome_how_it_works"), icon=":material/checklist:")
st.markdown(t("welcome_steps"))

get_started_col, chat_col = st.columns(2)
with get_started_col:
    if st.button(t("welcome_get_started_button"), icon=":material/arrow_forward:",
                 type="primary", width="stretch"):
        st.switch_page("pages/1_Start.py")
with chat_col:
    if st.button(t("welcome_chat_button"), icon=":material/arrow_forward:", width="stretch"):
        st.switch_page("pages/1_Chat.py")

st.caption(t("disclaimer"))
