"""HomeFit — starter page: injuries + the training plan your doctor prescribed."""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

import db  # noqa: E402
import planner  # noqa: E402
from core import current_settings  # noqa: E402

INJURY_PLACEHOLDER = "e.g. left knee — ACL repair 3 months ago, no deep flexion past 90°; stiff lower back"

PLAN_PLACEHOLDER = """e.g. 3 sessions per week for 6 weeks, post-ACL reconstruction (3 months out).

Day 1 — Quads & glutes
1. Seated knee extensions — 3 x 12 reps, 60 s rest between sets
2. Glute bridges — 3 x 15 reps, 45 s rest
3. Wall sits — 3 x 30 s hold, 60 s rest

Day 2 — Hip mobility & core
1. Standing hip circles — 2 x 10 reps each direction, 30 s rest
2. Dead bug — 3 x 30 s hold, 30 s rest
3. Side-lying clamshells — 3 x 15 reps each side, 30 s rest

Day 3 — Posterior chain (no loaded spinal flexion)
1. Prone hamstring curls — 3 x 12 reps, 45 s rest
2. Bird dog — 3 x 30 s hold each side, 30 s rest
3. Standing calf raises — 3 x 15 reps, 45 s rest"""

api_key, model, demo_mode = current_settings()

st.write("Tell us what's injured and what your doctor prescribed. "
         "We'll turn it into home exercises you can actually do.")

st.subheader("1 · Your injuries")
injuries = st.text_input(
    "What injuries or limitations do you have?",
    placeholder=INJURY_PLACEHOLDER,
    label_visibility="collapsed",
)

st.subheader("2 · The plan your doctor prescribed")
prescribed_plan = st.text_area(
    "Paste or type it as free text",
    height=320,
    placeholder=PLAN_PLACEHOLDER,
    label_visibility="collapsed",
)

st.divider()
generate_col, existing_col = st.columns([1, 2])
with generate_col:
    generate_clicked = st.button("Build my plan →", type="primary", width="stretch")
with existing_col:
    if planner.GENERATED_PLAN_PATH.exists():
        if st.button("Open my saved plan", width="content"):
            st.switch_page("pages/2_Your_plan.py")

if generate_clicked:
    if not prescribed_plan.strip():
        st.error("Add the prescribed training plan first — that's what the exercises are built from.")
    else:
        intake_id = db.save_intake(injuries, prescribed_plan)
        st.session_state["intake_id"] = intake_id
        with st.spinner("Turning your prescribed plan into home exercises…"):
            try:
                plan = planner.generate_plan(api_key, model, demo_mode, injuries, prescribed_plan)
                planner.save_plan(plan)
                db.attach_generated_plan(intake_id, plan)
            except Exception as error:
                st.error(f"Couldn't build the plan: {error}")
                plan = None
        if plan:
            st.session_state.pop("selected_day", None)
            st.session_state["substitutions"] = {}
            st.switch_page("pages/2_Your_plan.py")

saved_injuries = db.list_injuries()
if saved_injuries:
    with st.expander(f"Injuries saved so far ({len(saved_injuries)})"):
        st.dataframe(
            [{"Saved": row["created_at"], "Injuries": row["description"]}
             for row in saved_injuries],
            width="stretch", hide_index=True,
        )

st.caption("Not medical advice. Stop if you feel pain, and check that furniture is stable "
           "before loading it.")
