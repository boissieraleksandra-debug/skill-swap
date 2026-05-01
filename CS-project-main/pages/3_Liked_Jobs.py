"""
3_Liked_Jobs.py — Saved jobs the student liked, with one-click Apply.
"""

import streamlit as st

import ui
from db import (
    init_db,
    list_liked_jobs,
    get_job,
    get_student,
    get_startup,
    create_application,
)
from mailer import send_email
from templates import (
    application_confirm_student,
    application_notify_startup,
)

st.set_page_config(page_title="Saved · gigly", page_icon="g", layout="centered")
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

st.markdown("# Saved roles")
st.caption("Gigs you said yes to. Apply when you're ready — we'll email the startup for you.")
st.write("")

liked = list_liked_jobs(student_id)
if not liked:
    st.info(
        "Nothing saved yet. Open **Discover**, save a few gigs, "
        "and they'll show up here."
    )
    if st.button("Go to Discover", type="primary", use_container_width=True):
        st.switch_page("pages/2_Discovery.py")
    st.stop()

for job in liked:
    with st.container(border=True):
        if job["image_url"]:
            st.image(job["image_url"], use_container_width=True)

        st.caption(f"{job['startup_name']}  ·  {job['industry']}")
        st.markdown(f"### {job['title']}")
        st.caption(f"{job['location']}  ·  {job['duration']}")
        st.write(job["short_desc"])

        with st.expander("View full description"):
            st.markdown("**About this role**")
            st.write(job["long_desc"])
            st.markdown("**What we're looking for**")
            st.write(job["requirements"])
            st.markdown(f"**Pay:**  {job['pay_rate']}")

        already_applied = bool(job["already_applied"])

        if already_applied:
            st.success("Applied — we'll email you when the startup decides.")
            continue

        if st.button("Apply", key=f"apply_{job['id']}",
                     type="primary", use_container_width=True):
            app_id = create_application(student_id, job["id"])
            if app_id is None:
                st.warning("Already applied.")
                st.rerun()

            student = get_student(student_id)
            full_job = get_job(job["id"])
            startup = get_startup(full_job["startup_id"])

            subject, body = application_confirm_student(student, full_job, startup)
            send_email(student["email"], subject, body)

            subject2, body2 = application_notify_startup(student, full_job, startup)
            send_email(startup["email"], subject2, body2)

            st.toast("Application sent.")
            st.rerun()
