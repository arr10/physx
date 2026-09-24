"""HomeFit — chat intake: a conversational alternative to the Start form."""
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

import db  # noqa: E402
import planner  # noqa: E402
from core import (CHAT_DEMO_PROMPTS, CHAT_INTAKE_SYSTEM_PROMPT, call_openai_chat,  # noqa: E402
                  current_settings, extract_intake_from_chat)

api_key, model, demo_mode = current_settings()
offline = demo_mode or not api_key

st.write("Tell us about your injury a little at a time, back and forth — we'll turn the "
         "conversation into a home training plan.")

st.session_state.setdefault("chat_messages", [])
messages = st.session_state["chat_messages"]

for message in messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if not messages:
    with st.chat_message("assistant"):
        st.write(CHAT_DEMO_PROMPTS[0] if offline else
                 "Hi! What's injured, and how long ago did it happen?")

prompt = st.chat_input("Tell me what's going on…")
if prompt:
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        if offline:
            turn = sum(1 for m in messages if m["role"] == "user") - 1
            reply = CHAT_DEMO_PROMPTS[min(turn, len(CHAT_DEMO_PROMPTS) - 1)]
            st.write(reply)
        else:
            chat_payload = [{"role": "system", "content": CHAT_INTAKE_SYSTEM_PROMPT}] + messages
            reply = st.write_stream(call_openai_chat(api_key, model, chat_payload))
    messages.append({"role": "assistant", "content": reply})

st.divider()
if st.button("Build my plan from this conversation →", type="primary", disabled=not messages):
    with st.spinner("Turning your conversation into a plan…"):
        try:
            if offline:
                injuries_text = " ".join(m["content"] for m in messages if m["role"] == "user")
                plan_text = "(From chat) See the conversation above for context."
            else:
                intake = extract_intake_from_chat(api_key, model, messages)
                injuries_text = intake.get("injuries_text", "")
                plan_text = intake.get("plan_text", "") or "(From chat) See the conversation above."
            intake_id = db.save_intake(injuries_text, plan_text)
            st.session_state["intake_id"] = intake_id
            plan = planner.generate_plan(api_key, model, demo_mode, injuries_text, plan_text)
            planner.save_plan(plan)
            db.attach_generated_plan(intake_id, plan)
        except Exception as error:
            st.error(f"Couldn't build the plan: {error}")
            plan = None
    if plan:
        st.session_state.pop("selected_day", None)
        st.session_state["substitutions"] = {}
        st.switch_page("pages/2_Your_plan.py")
