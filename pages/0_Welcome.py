"""HomeFit — landing page: explains the concept before the intake form."""
import streamlit as st

st.write(
    "HomeFit turns the training plan your doctor prescribed into a home workout "
    "you can actually do — using whatever equipment you already have."
)

st.subheader("How it works")
st.markdown(
    "1. **Tell us what's injured** — paste the plan your doctor prescribed, or talk it "
    "through with our AI coach if you don't have one yet.\n"
    "2. **We turn it into home exercises** matched to your equipment, injuries, and goals.\n"
    "3. **Swap out anything you don't have** — HomeFit suggests household substitutes on the spot."
)

st.divider()

get_started_col, chat_col = st.columns(2)
with get_started_col:
    if st.button("Get started →", type="primary", width="stretch"):
        st.switch_page("pages/1_Start.py")
with chat_col:
    if st.button("Or chat with our AI coach →", width="stretch"):
        st.switch_page("pages/1_Chat.py")

st.caption("Not medical advice. Stop if you feel pain, and check that furniture is stable "
           "before loading it.")
