"""
8_Startup_Dashboard.py — Startup status & insights.
"""

from collections import Counter, defaultdict

import plotly.express as px
import streamlit as st

import ui
from db import (
    init_db,
    list_jobs_for_startup,
    list_applications_for_startup,
)

st.set_page_config(page_title="Dashboard · gigly", page_icon="g", layout="centered")
init_db()
ui.load_css()
ui.sidebar()

# ---- Auth guard ---------------------------------------------------------
if st.session_state.get("role") != "startup" or not st.session_state.get("startup_id"):
    st.warning("Please create your company profile first.")
    if st.button("Go to Company", type="primary", use_container_width=True):
        st.switch_page("pages/5_Startup_Profile.py")
    st.stop()

startup_id = st.session_state["startup_id"]

st.markdown("# Dashboard")
st.caption("Listings and applicants at a glance.")
st.write("")

jobs = list_jobs_for_startup(startup_id)
apps = list_applications_for_startup(startup_id)

# ---- KPI tiles -----------------------------------------------------------
total_jobs    = len(jobs)
total_apps    = len(apps)
pending_apps  = sum(1 for a in apps if a["status"] == "pending")
accepted_apps = sum(1 for a in apps if a["status"] == "accepted")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Listings",   total_jobs)
c2.metric("Total apps", total_apps)
c3.metric("Pending",    pending_apps)
c4.metric("Accepted",   accepted_apps)

st.write("")

# ---- Bar chart: applications per listing --------------------------------
if jobs:
    st.markdown("### Applications per listing")
    apps_by_job_id = Counter(a["job_id"] for a in apps)
    chart_data = [
        {
            "job": (j["title"][:30] + "…") if len(j["title"]) > 30 else j["title"],
            "applications": apps_by_job_id.get(j["id"], 0),
        }
        for j in jobs
    ]
    fig = px.bar(
        chart_data,
        x="job",
        y="applications",
        color="applications",
        color_continuous_scale=["#EDE5FC", "#A78BFA", "#7C3AED", "#5B21B6"],
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        showlegend=False,
        coloraxis_showscale=False,
        yaxis_title=None,
        xaxis_title=None,
        font=dict(family="Inter, -apple-system, sans-serif", color="#1B1530"),
    )
    st.plotly_chart(fig, use_container_width=True)

st.write("")

# ---- Per-job detailed breakdown -----------------------------------------
JOB_STATUS_PILL = {
    "open":        ("open",        "Open"),
    "in_progress": ("in_progress", "In progress"),
    "done":        ("done",        "Done"),
}
APP_STATUS_PILL = {
    "pending":   ("pending",   "Pending"),
    "accepted":  ("accepted",  "Accepted (in progress)"),
    "declined":  ("declined",  "Declined"),
    "completed": ("completed", "Completed"),
}

st.markdown("### Per-listing breakdown")

if not jobs:
    st.info("Post your first role from the Listings page to see status here.")
    st.stop()

apps_by_job = defaultdict(list)
for a in apps:
    apps_by_job[a["job_id"]].append(a)

for job in jobs:
    job_apps = apps_by_job.get(job["id"], [])
    by_status = defaultdict(list)
    for a in job_apps:
        by_status[a["status"]].append(a)

    with st.container(border=True):
        head_l, head_r = st.columns([3, 1])
        with head_l:
            st.markdown(f"**{job['title']}**")
            cls, label = JOB_STATUS_PILL.get(job["status"], ("", job["status"]))
            st.markdown(
                f"<span class='status-pill {cls}'>{label}</span>",
                unsafe_allow_html=True,
            )
        with head_r:
            st.markdown(f"### {len(job_apps)}")
            st.caption("apps")

        if not job_apps:
            st.caption("No applications yet.")
            continue

        for status_key, (cls, status_label) in APP_STATUS_PILL.items():
            people = by_status.get(status_key, [])
            if not people:
                continue
            with st.expander(f"{status_label} · {len(people)}"):
                for a in people:
                    st.write(f"• **{a['student_name']}** — {a['student_email']}")
