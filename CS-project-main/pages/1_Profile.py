"""
1_Profile.py — Student profile page (signup OR view/edit).

Two modes, picked at runtime:

1. No student_id in session_state → show the **signup form**.
   On submit: insert the student, send a welcome email, save the
   new id in session, and continue to the Job Feed (Discovery).

2. student_id present → show the **profile** in read-only mode with
   an "Edit" button that switches the same fields into a save-able form.

The signup form is intentionally short so a student can finish in
roughly a minute. The Interests multiselect doubles as input to the
TF-IDF recommender (Phase I).
"""

from pathlib import Path

import streamlit as st

import ui
from db import (
    init_db,
    create_student,
    update_student,
    get_student,
    get_student_by_email,
)
from mailer import send_email
from templates import signup_confirm_student

# ---- Page setup ----------------------------------------------------------
st.set_page_config(page_title="Profile · gigly", page_icon="g", layout="centered")
init_db()
ui.load_css()
ui.sidebar()

# Visiting this page directly counts as picking "I'm a student".
if st.session_state.get("role") != "student":
    st.session_state["role"] = "student"

# Where uploaded CVs are saved on disk. Created once.
UPLOADS = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS.mkdir(exist_ok=True)

# Lists used by the form. Edit freely — adding values doesn't break anything.
INTEREST_CHOICES = [
    "Marketing", "Sales", "Finance", "Tech", "Software Engineering",
    "Data & Analytics", "Design", "UX/UI", "Sustainability", "Climate",
    "Operations", "Customer Success", "Content & Writing", "Strategy",
    "Product", "Research",
]
AVAILABILITY_CHOICES = [
    "5-10 hrs / week",
    "10-20 hrs / week",
    "20-30 hrs / week",
    "Full-time",
    "Project-based",
]


def _save_cv(cv_file, student_id: int) -> str | None:
    """Save the uploaded CV to uploads/student_<id>.<ext> and return the filename."""
    if cv_file is None:
        return None
    ext = Path(cv_file.name).suffix.lower() or ".pdf"
    out = UPLOADS / f"student_{student_id}{ext}"
    out.write_bytes(cv_file.getbuffer())
    return out.name


# =========================================================================
# Mode 1: viewing / editing an existing profile
# =========================================================================

if st.session_state.get("student_id"):
    student = get_student(st.session_state["student_id"])

    if not student:
        # Stale session (db was wiped) — clear and fall through to signup.
        st.session_state.pop("student_id", None)
    else:
        st.markdown("# Your profile")
        st.caption("Manage how startups see you.")

        editing = st.session_state.get("profile_editing", False)

        # --- Read-only view ---
        if not editing:
            st.markdown(f"**Name:**  {student['name']}")
            st.markdown(f"**Email:**  {student['email']}")
            st.markdown(f"**LinkedIn:**  {student['linkedin'] or '—'}")
            st.markdown(f"**Education:**  {student['education'] or '—'}")
            st.markdown(f"**Interests:**  {student['interests'] or '—'}")
            st.markdown(f"**Availability:**  {student['availability'] or '—'}")
            st.markdown(f"**CV:**  {student['cv_filename'] or '—'}")

            if st.button("Edit profile", type="primary", use_container_width=True):
                st.session_state["profile_editing"] = True
                st.rerun()

            st.stop()

        # --- Edit form ---
        with st.form("edit_profile"):
            name = st.text_input("Full name", value=student["name"] or "")
            linkedin = st.text_input("LinkedIn URL", value=student["linkedin"] or "")
            education = st.text_input(
                "Education",
                value=student["education"] or "",
                placeholder="BSc Business, ETH Zurich, 4th semester",
            )
            current_interests = [
                i.strip() for i in (student["interests"] or "").split(",") if i.strip()
            ]
            interests = st.multiselect(
                "Interests",
                INTEREST_CHOICES,
                default=[i for i in current_interests if i in INTEREST_CHOICES],
            )
            availability_idx = (
                AVAILABILITY_CHOICES.index(student["availability"])
                if student["availability"] in AVAILABILITY_CHOICES
                else 0
            )
            availability = st.selectbox(
                "Availability", AVAILABILITY_CHOICES, index=availability_idx
            )
            cv_file = st.file_uploader("Replace CV (PDF)", type=["pdf"])

            col_a, col_b = st.columns(2)
            with col_a:
                saved = st.form_submit_button("Save", type="primary", use_container_width=True)
            with col_b:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state["profile_editing"] = False
            st.rerun()

        if saved:
            updates = {
                "name": name.strip(),
                "linkedin": linkedin.strip() or None,
                "education": education.strip() or None,
                "interests": ", ".join(interests) or None,
                "availability": availability,
            }
            if cv_file is not None:
                updates["cv_filename"] = _save_cv(cv_file, student["id"])
            update_student(student["id"], **updates)
            st.session_state["profile_editing"] = False
            st.success("Profile updated.")
            st.rerun()

        st.stop()


# =========================================================================
# Mode 2: signup form (no student_id in session)
# =========================================================================

st.markdown("# Create your profile")
st.caption("Takes about a minute. We use it to surface the right roles for you.")

with st.form("signup"):
    name = st.text_input("Full name *")
    email = st.text_input("Email *")
    linkedin = st.text_input(
        "LinkedIn URL", placeholder="https://linkedin.com/in/yourname"
    )
    education = st.text_input(
        "Education",
        placeholder="BSc Business, ETH Zurich, 4th semester",
    )
    interests = st.multiselect("Interests", INTEREST_CHOICES)
    availability = st.selectbox("Availability", AVAILABILITY_CHOICES)
    cv_file = st.file_uploader("CV (PDF, optional)", type=["pdf"])

    submitted = st.form_submit_button(
        "Create profile", type="primary", use_container_width=True
    )

if submitted:
    # Minimal validation — name + email are required.
    if not name.strip() or not email.strip():
        st.error("Name and email are required.")
        st.stop()

    # If this email already has a profile, sign them back in (no passwords
    # in the prototype — auth is intentionally out of scope).
    existing = get_student_by_email(email.strip())
    if existing:
        st.session_state["role"] = "student"
        st.session_state["student_id"] = existing["id"]
        st.info("Welcome back! We found your existing profile.")
        st.switch_page("pages/2_Discovery.py")

    # New signup: insert first (so we have an id for the CV filename).
    sid = create_student(
        name=name.strip(),
        email=email.strip(),
        linkedin=linkedin.strip() or None,
        cv_filename=None,
        education=education.strip() or None,
        interests=", ".join(interests) or None,
        availability=availability,
    )
    if cv_file is not None:
        cv_name = _save_cv(cv_file, sid)
        update_student(sid, cv_filename=cv_name)

    # Remember who we are for the rest of the session.
    st.session_state["role"] = "student"
    st.session_state["student_id"] = sid

    # Send the welcome email (real or simulated, depending on .env).
    student_row = get_student(sid)
    subject, body = signup_confirm_student(student_row)
    send_email(student_row["email"], subject, body)

    st.success("Profile created. Check your inbox for the welcome email.")
    st.switch_page("pages/2_Discovery.py")
