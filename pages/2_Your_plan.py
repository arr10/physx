"""HomeFit — the generated plan, read from generated_plan.json."""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

import db  # noqa: E402
import planner  # noqa: E402
from core import current_settings, render_daily_plan  # noqa: E402
from i18n import get_language, t  # noqa: E402
from pdf_export import build_plan_pdf  # noqa: E402


@st.cache_data(show_spinner=False)
def plan_pdf(plan_json: str, subtitle: str, language: str) -> bytes:
    """Cached on the plan itself, so reruns don't re-render the document."""
    return build_plan_pdf(json.loads(plan_json), subtitle, language)


api_key, model, demo_mode = current_settings()
st.title(t("plan_title"))

plan = planner.load_saved_plan()
if not plan or not plan.get("exercises"):
    st.warning(t("plan_warning_no_plan"))
    if st.button(t("plan_go_to_start_button"), type="primary"):
        st.switch_page("pages/1_Start.py")
    st.stop()

intake = db.latest_intake()
pdf_subtitle = ""
if intake:
    injuries = db.injuries_text(intake["id"])
    pdf_subtitle = t("plan_pdf_subtitle", injuries=injuries) if injuries else ""
    st.caption(t("plan_built_from_caption", date=intake["created_at"])
               + (t("plan_injuries_suffix", injuries=injuries) if injuries else ""))
    with st.expander(t("plan_prescribed_expander")):
        st.write(intake["plan_text"])

st.subheader(t("plan_daily_subheader"))
st.write(t("plan_daily_intro"))
render_daily_plan(plan["exercises"], api_key, model, demo_mode)

st.divider()
left_col, right_col = st.columns([1, 1])
with left_col:
    if st.button(t("plan_edit_button")):
        st.switch_page("pages/1_Start.py")
with right_col:
    st.download_button(
        t("plan_download_button"),
        data=plan_pdf(json.dumps(plan, ensure_ascii=False, sort_keys=True), pdf_subtitle,
                      get_language()),
        file_name="training-plan.pdf",
        mime="application/pdf",
    )

st.caption(t("disclaimer"))
