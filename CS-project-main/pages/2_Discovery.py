"""
2_Discovery.py — Job Feed (the student's main page).

Shows up to 8 jobs the student hasn't decided on yet, ranked by
the TF-IDF + cosine recommender in `recommender.py`.
"""

import streamlit as st

import ui
from db import init_db, record_swipe
from recommender import recommend_jobs

st.set_page_config(page_title="Discover · gigly", page_icon="g", layout="centered")
init_db()
ui.load_css()
ui.sidebar()

# ---- Auth guard: students only -----------------------------------------
if st.session_state.get("role") != "student" or not st.session_state.get("student_id"):
    st.warning("Please create your student profile first.")
    if st.button("Go to Profile", type="primary", use_container_width=True):
        st.switch_page("pages/1_Profile.py")
    st.stop()

student_id = st.session_state["student_id"]

# ---- Header + refresh ---------------------------------------------------
header_l, header_r = st.columns([4, 1])
with header_l:
    st.markdown("# Discover")
with header_r:
    st.write("")
    if st.button("Refresh", help="Re-rank the feed", use_container_width=True):
        st.session_state.pop("expanded_job", None)
        st.rerun()

st.caption("Save the gigs you'd actually take. We learn from what you pick.")
st.write("")

# ---- Get ranked recommendations ----------------------------------------
MAX_CARDS = 8
ranked = recommend_jobs(student_id, max_results=MAX_CARDS)

if not ranked:
    st.info(
        "You've seen every gig in the feed. "
        "Head to **Saved** to apply — or come back when new ones are posted."
    )
    st.stop()

expanded_job_id = st.session_state.get("expanded_job")

# ---- Render each card ---------------------------------------------------
for job, match_pct, why in ranked:
    with st.container(border=True):

        if job["image_url"]:
            st.image(job["image_url"], use_container_width=True)

        head_l, head_r = st.columns([3, 1])
        with head_l:
            st.caption(f"{job['startup_name']}  ·  {job['industry']}")
        with head_r:
            st.markdown(
                f"<div style='text-align:right'>"
                f"<span class='score-pill'>{match_pct}% match</span></div>",
                unsafe_allow_html=True,
            )

        st.markdown(f"### {job['title']}")
        st.caption(f"{job['location']}  ·  {job['duration']}")

        if why:
            st.caption(f"_Matches your: {', '.join(why)}_")

        st.write(job["short_desc"])

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Details", key=f"view_{job['id']}",
                         use_container_width=True):
                record_swipe(student_id, job["id"], "click")
                st.session_state["expanded_job"] = job["id"]
                st.rerun()
        with c2:
            if st.button("Save", key=f"like_{job['id']}",
                         type="primary", use_container_width=True):
                record_swipe(student_id, job["id"], "like")
                st.session_state.pop("expanded_job", None)
                st.rerun()
        with c3:
            if st.button("Pass", key=f"dislike_{job['id']}",
                         use_container_width=True):
                record_swipe(student_id, job["id"], "dislike")
                st.session_state.pop("expanded_job", None)
                st.rerun()

        if expanded_job_id == job["id"]:
            st.divider()
            st.markdown("**About this role**")
            st.write(job["long_desc"])
            st.markdown("**What we're looking for**")
            st.write(job["requirements"])
            st.markdown(f"**Pay:**  {job['pay_rate']}")
