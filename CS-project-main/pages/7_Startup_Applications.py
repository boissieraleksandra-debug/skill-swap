"""
7_Startup_Applications.py — Review applicants and accept / decline.
"""

from urllib.parse import quote

import streamlit as st

import ui
from db import (
    init_db,
    list_applications_for_startup,
    get_application,
    get_startup,
    update_application_status,
)
from mailer import send_email
from templates import acceptance_email, rejection_email

st.set_page_config(page_title="Applicants · gigly", page_icon="g", layout="centered")
init_db()
ui.load_css()
ui.sidebar()

# ---- Auth guard: startups only -----------------------------------------
if st.session_state.get("role") != "startup" or not st.session_state.get("startup_id"):
    st.warning("Please create your company profile first.")
    if st.button("Go to Company", type="primary", use_container_width=True):
        st.switch_page("pages/5_Startup_Profile.py")
    st.stop()

startup_id = st.session_state["startup_id"]


def avatar_url(name: str) -> str:
    """Initial-based avatar with a purple background to match the brand."""
    safe = quote(name or "Applicant")
    return (
        f"https://ui-avatars.com/api/?name={safe}"
        "&size=240&background=7C3AED&color=ffffff&rounded=true&bold=true"
    )


STATUS_PILL = {
    "pending":   ("pending",   "Pending"),
    "accepted":  ("accepted",  "Accepted"),
    "declined":  ("declined",  "Declined"),
    "completed": ("completed", "Completed"),
}


def status_html(status: str) -> str:
    cls, label = STATUS_PILL.get(status, ("", status))
    return f"<span class='status-pill {cls}'>{label}</span>"


# =========================================================================
# DETAIL view: viewing one applicant
# =========================================================================

viewing_id = st.session_state.get("viewing_application_id")

if viewing_id:
    app = get_application(viewing_id)
    if not app:
        st.warning("Application not found.")
        st.session_state.pop("viewing_application_id", None)
        st.stop()

    if st.button("← Back to applicants"):
        st.session_state.pop("viewing_application_id", None)
        st.rerun()

    header_l, header_r = st.columns([1, 2])
    with header_l:
        st.image(avatar_url(app["student_name"]), width=120)
    with header_r:
        st.markdown(f"### {app['student_name']}")
        st.caption(f"Applied for **{app['job_title']}**  ·  {app['industry']}")
        st.markdown(status_html(app["status"]), unsafe_allow_html=True)

    st.write("")
    st.markdown(f"**Email:**  {app['student_email']}")
    st.markdown(f"**LinkedIn:**  {app['linkedin'] or '—'}")
    st.markdown(f"**Education:**  {app['education'] or '—'}")
    st.markdown(f"**Interests:**  {app['interests'] or '—'}")
    st.markdown(f"**Availability:**  {app['availability'] or '—'}")
    st.markdown(f"**CV:**  {app['cv_filename'] or '—'}")

    st.write("")

    if app["status"] == "pending":
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Accept", key="accept_btn",
                         type="primary", use_container_width=True):
                update_application_status(app["id"], "accepted")

                student = {"name": app["student_name"], "email": app["student_email"]}
                job = {"title": app["job_title"]}
                startup_row = get_startup(startup_id)

                subj, body = acceptance_email(student, job, startup_row)
                send_email(student["email"], subj, body)

                st.toast("Accepted. Acceptance email sent.")
                st.session_state.pop("viewing_application_id", None)
                st.rerun()

        with c2:
            if st.button("Decline", key="decline_btn", use_container_width=True):
                update_application_status(app["id"], "declined")

                student = {"name": app["student_name"], "email": app["student_email"]}
                job = {"title": app["job_title"]}
                startup_row = get_startup(startup_id)

                subj, body = rejection_email(student, job, startup_row)
                send_email(student["email"], subj, body)

                st.toast("Declined. Rejection email sent.")
                st.session_state.pop("viewing_application_id", None)
                st.rerun()
    else:
        st.info(f"This application is already **{app['status']}**.")

    st.stop()


# =========================================================================
# LIST view
# =========================================================================

st.markdown("# Applicants")
st.caption("New and past applications across all your listings.")
st.write("")

apps = list_applications_for_startup(startup_id)
if not apps:
    st.info("No applications yet. Once a student applies you'll see them here.")
    st.stop()

filter_choice = st.selectbox(
    "Filter",
    ["All", "Pending", "Accepted", "Declined"],
    key="app_filter",
)
filter_map = {
    "All":      None,
    "Pending":  "pending",
    "Accepted": "accepted",
    "Declined": "declined",
}
filter_status = filter_map[filter_choice]
filtered = [a for a in apps if filter_status is None or a["status"] == filter_status]

if not filtered:
    st.info(f"No applications matching '{filter_choice}'.")
    st.stop()

for app in filtered:
    with st.container(border=True):
        cols = st.columns([1, 3])
        with cols[0]:
            st.image(avatar_url(app["student_name"]), width=80)
        with cols[1]:
            st.markdown(f"**{app['student_name']}**")
            st.caption(f"Applied for *{app['job_title']}*")
            st.markdown(status_html(app["status"]), unsafe_allow_html=True)

        if st.button(
            "Open profile",
            key=f"open_{app['id']}",
            use_container_width=True,
        ):
            st.session_state["viewing_application_id"] = app["id"]
            st.rerun()
