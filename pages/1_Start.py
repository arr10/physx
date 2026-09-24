"""HomeFit — starter page: injuries + the training plan your doctor prescribed."""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

import db  # noqa: E402
import planner  # noqa: E402
from core import current_settings  # noqa: E402
from i18n import t  # noqa: E402

api_key, model, demo_mode = current_settings()

st.write(t("start_intro"))

st.subheader(t("start_injuries_subheader"))
injuries = st.text_input(
    t("start_injuries_label"),
    placeholder=t("start_injuries_placeholder"),
    label_visibility="collapsed",
)

st.subheader(t("start_plan_subheader"))
prescribed_plan = st.text_area(
    t("start_plan_label"),
    height=320,
    placeholder=t("start_plan_placeholder"),
    label_visibility="collapsed",
)

st.divider()
generate_col, existing_col = st.columns([1, 2])
with generate_col:
    generate_clicked = st.button(t("start_build_button"), type="primary", width="stretch")
with existing_col:
    if planner.GENERATED_PLAN_PATH.exists():
        if st.button(t("start_open_saved_button"), width="content"):
            st.switch_page("pages/2_Your_plan.py")

if generate_clicked:
    if not prescribed_plan.strip():
        st.error(t("start_error_no_plan"))
    else:
        intake_id = db.save_intake(injuries, prescribed_plan)
        st.session_state["intake_id"] = intake_id
        with st.spinner(t("start_spinner_building")):
            try:
                plan = planner.generate_plan(api_key, model, demo_mode, injuries, prescribed_plan)
                planner.save_plan(plan)
                db.attach_generated_plan(intake_id, plan)
            except Exception as error:
                st.error(t("couldnt_build_plan", error=error))
                plan = None
        if plan:
            st.session_state.pop("selected_day", None)
            st.session_state["substitutions"] = {}
            st.switch_page("pages/2_Your_plan.py")

saved_injuries = db.list_injuries()
if saved_injuries:
    with st.expander(t("start_saved_injuries_expander", n=len(saved_injuries))):
        st.dataframe(
            [{t("start_saved_col"): row["created_at"], t("start_injuries_col"): row["description"]}
             for row in saved_injuries],
            width="stretch", hide_index=True,
        )

st.caption(t("disclaimer"))
