"""
4_Student_Dashboard.py — The student's status & insights page.
"""

from collections import Counter

import plotly.express as px
import streamlit as st

import ui
from db import (
    init_db,
    list_applications_for_student,
    list_liked_jobs,
)

st.set_page_config(page_title="Dashboard · gigly", page_icon="g", layout="centered")
init_db()
ui.load_css()
ui.sidebar()

# ---- Auth guard ---------------------------------------------------------
if st.session_state.get("role") != "student" or not st.session_state.get("student_id"):
    st.warning("Please create your student profile first.")
    if st.button("Go to Profile", type="primary", use_container_width=True):
        st.switch_page("pages/1_Profile.py")
    st.stop()

student_id = st.session_state["student_id"]

st.markdown("# Dashboard")
st.caption("How your applications are going.")
st.write("")

apps = list_applications_for_student(student_id)
liked = list_liked_jobs(student_id)

# ---- KPI tiles ----------------------------------------------------------
status_counts = Counter(a["status"] for a in apps)
total       = len(apps)
pending     = status_counts.get("pending",   0)
in_progress = status_counts.get("accepted",  0)
completed   = status_counts.get("completed", 0)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Applied",     total)
c2.metric("Pending",     pending)
c3.metric("In progress", in_progress)
c4.metric("Completed",   completed)

st.write("")

# Purple-leaning palettes for the charts.
PURPLE_PALETTE = {
    "Pending":                "#A78BFA",
    "Accepted (in progress)": "#7C3AED",
    "Completed":              "#5B21B6",
    "Declined":               "#C4B5FD",
}

INDUSTRY_PALETTE = {
    "Marketing":      "#EC4899",
    "Tech":           "#7C3AED",
    "Finance":        "#10B981",
    "Sustainability": "#06B6D4",
    "Design":         "#A78BFA",
}

# ---- Donut chart: status breakdown --------------------------------------
if total > 0:
    st.markdown("### Application status")
    chart_data = [
        {"status": label, "count": status_counts.get(key, 0)}
        for key, label in [
            ("pending",   "Pending"),
            ("accepted",  "Accepted (in progress)"),
            ("completed", "Completed"),
            ("declined",  "Declined"),
        ]
        if status_counts.get(key, 0) > 0
    ]
    fig = px.pie(
        chart_data,
        names="status",
        values="count",
        hole=0.6,
        color="status",
        color_discrete_map=PURPLE_PALETTE,
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        showlegend=True,
        font=dict(family="Inter, -apple-system, sans-serif", color="#1B1530"),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Apply to a few roles to see your status breakdown here.")

st.write("")

# ---- Bar chart: liked jobs by industry ----------------------------------
if liked:
    st.markdown("### Saved roles by industry")
    industry_counts = Counter(j["industry"] for j in liked if j["industry"])
    chart_data2 = sorted(
        [{"industry": k, "count": v} for k, v in industry_counts.items()],
        key=lambda r: r["count"], reverse=True,
    )
    fig2 = px.bar(
        chart_data2,
        x="industry",
        y="count",
        color="industry",
        color_discrete_map=INDUSTRY_PALETTE,
    )
    fig2.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        showlegend=False,
        yaxis_title=None,
        xaxis_title=None,
        font=dict(family="Inter, -apple-system, sans-serif", color="#1B1530"),
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Save a few roles in Discover to see your interests visualized here.")

st.write("")

# ---- Detailed application list ------------------------------------------
st.markdown("### All applications")
if not apps:
    st.caption("You haven't applied to anything yet.")
else:
    STATUS_PILL = {
        "pending":   ("pending",   "Pending",   "Waiting for the startup to decide."),
        "accepted":  ("accepted",  "Accepted",  "Check your email — the startup sent contact info."),
        "declined":  ("declined",  "Declined",  "Better luck next time."),
        "completed": ("completed", "Completed", "Job done."),
    }
    for a in apps:
        cls, label, hint = STATUS_PILL.get(a["status"], ("", "—", ""))
        with st.container(border=True):
            st.markdown(f"**{a['job_title']}** — *{a['startup_name']}*")
            st.markdown(
                f"<span class='status-pill {cls}'>{label}</span>"
                f" <span style='color:#8E8AA8;font-size:0.82rem'>"
                f"applied {a['created_at'][:10]}</span>",
                unsafe_allow_html=True,
            )
            st.caption(hint)
