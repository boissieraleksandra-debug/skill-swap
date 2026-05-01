"""
app.py — Landing page (the very first screen).

Users pick their role here. Their choice is stored in
st.session_state and used by every other page to decide what to show.

We also call init_db() on every run so a teammate who clones the repo
and just runs `streamlit run app.py` (forgetting `python seed.py`) at
least gets an empty-but-valid database. Sample jobs still need seed.py.
"""

import streamlit as st

import ui
from db import init_db

st.set_page_config(
    page_title="gigly — students × startups",
    page_icon="g",
    layout="centered",
    initial_sidebar_state="collapsed",
)

init_db()
ui.load_css()
ui.sidebar()

# ---- Hero ---------------------------------------------------------------
st.markdown(
    """
    <div class='gigly-hero'>
      <div class='gigly-hero-mark'>gigly</div>
      <div class='gigly-hero-sub'>Where students and startups build together.</div>
      <div class='gigly-hero-meta'>Short-term roles. Real work. No noise.</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# ---- Already logged in? Offer a continue link --------------------------
role = st.session_state.get("role")

if role == "student" and st.session_state.get("student_id"):
    st.success("Signed in as a student.")
    if st.button("Continue to Discover", type="primary", use_container_width=True):
        st.switch_page("pages/2_Discovery.py")
    if st.button("Log out", use_container_width=True):
        for k in ("role", "student_id", "startup_id", "profile_editing"):
            st.session_state.pop(k, None)
        st.rerun()
    st.stop()

if role == "startup" and st.session_state.get("startup_id"):
    st.success("Signed in as a startup.")
    if st.button("Continue to Listings", type="primary", use_container_width=True):
        st.switch_page("pages/6_Startup_Listings.py")
    if st.button("Log out", use_container_width=True):
        for k in ("role", "student_id", "startup_id",
                  "profile_editing", "startup_editing"):
            st.session_state.pop(k, None)
        st.rerun()
    st.stop()

# ---- Role picker -------------------------------------------------------
st.markdown("### Get started")

col1, col2 = st.columns(2)

with col1:
    if st.button("I'm a student", use_container_width=True, type="primary"):
        st.session_state["role"] = "student"
        st.switch_page("pages/1_Profile.py")

with col2:
    if st.button("I'm a startup", use_container_width=True):
        st.session_state["role"] = "startup"
        st.switch_page("pages/5_Startup_Profile.py")

st.write("")
st.caption(
    "Students build a profile, browse a personalized feed, and apply with one click. "
    "Startups post listings, review applicants, and hire fast."
)
