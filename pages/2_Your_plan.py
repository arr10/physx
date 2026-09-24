"""HomeFit — the generated plan, read from generated_plan.json."""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

import db  # noqa: E402
import planner  # noqa: E402
from core import current_settings, render_daily_plan  # noqa: E402
from pdf_export import build_plan_pdf  # noqa: E402


@st.cache_data(show_spinner=False)
def plan_pdf(plan_json: str, subtitle: str) -> bytes:
    """Cached on the plan itself, so reruns don't re-render the document."""
    return build_plan_pdf(json.loads(plan_json), subtitle)


api_key, model, demo_mode = current_settings()
st.title("Your plan")

plan = planner.load_saved_plan()
if not plan or not plan.get("exercises"):
    st.warning("No plan yet. Start by telling us about your injuries and what your doctor prescribed.")
    if st.button("← Go to the start page", type="primary"):
        st.switch_page("pages/1_Start.py")
    st.stop()

intake = db.latest_intake()
pdf_subtitle = ""
if intake:
    injuries = db.injuries_text(intake["id"])
    pdf_subtitle = f"Injuries: {injuries}" if injuries else ""
    st.caption(f"Built from your intake on {intake['created_at']}"
               + (f" · Injuries: {injuries}" if injuries else ""))
    with st.expander("The plan your doctor prescribed"):
        st.write(intake["plan_text"])

st.subheader("Daily plan")
st.write("Choose a day to see your exercises. Select an exercise to open its instructions and media.")
render_daily_plan(plan["exercises"], api_key, model, demo_mode)

st.divider()
left_col, right_col = st.columns([1, 1])
with left_col:
    if st.button("← Edit injuries / prescribed plan"):
        st.switch_page("pages/1_Start.py")
with right_col:
    st.download_button(
        "Download plan PDF",
        data=plan_pdf(json.dumps(plan, ensure_ascii=False, sort_keys=True), pdf_subtitle),
        file_name="training-plan.pdf",
        mime="application/pdf",
    )

st.caption("Not medical advice. Stop if you feel pain, and check that furniture is stable "
           "before loading it.")
