"""
5_Startup_Profile.py — Startup company profile (signup OR view/edit).

Mirrors 1_Profile.py for students with the same two-mode pattern:
  - No startup_id in session  → signup form, then welcome email,
                                then redirect to the Listings page.
  - startup_id present        → read-only view + Edit toggle.

Direct-navigation to this page also implicitly sets the role to
"startup", so the app reacts correctly even if the user lands here
from a deep link or the sidebar nav.
"""

from pathlib import Path

import streamlit as st

import ui
from db import (
    init_db,
    create_startup,
    update_startup,
    get_startup,
    get_startup_by_email,
)
from mailer import send_email
from templates import signup_confirm_startup

# ---- Page setup ----------------------------------------------------------
st.set_page_config(page_title="Company · gigly", page_icon="g", layout="centered")
init_db()
ui.load_css()
ui.sidebar()

# Visiting this page directly counts as picking "I'm a startup".
if st.session_state.get("role") != "startup":
    st.session_state["role"] = "startup"

UPLOADS = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS.mkdir(exist_ok=True)

INDUSTRY_CHOICES = [
    "Marketing", "Tech", "Finance", "Sustainability", "Design", "Other",
]


def _save_logo(logo_file, startup_id: int) -> str | None:
    """Save the uploaded logo as uploads/startup_<id>.<ext>; return the filename."""
    if logo_file is None:
        return None
    ext = Path(logo_file.name).suffix.lower() or ".png"
    out = UPLOADS / f"startup_{startup_id}{ext}"
    out.write_bytes(logo_file.getbuffer())
    return out.name


# =========================================================================
# Mode 1: viewing / editing an existing profile
# =========================================================================

if st.session_state.get("startup_id"):
    startup = get_startup(st.session_state["startup_id"])

    if not startup:
        st.session_state.pop("startup_id", None)            # stale session
    else:
        st.markdown(f"# {startup['name']}")
        st.caption("Your company profile.")

        editing = st.session_state.get("startup_editing", False)

        if not editing:
            st.markdown(f"**Industry:**  {startup['industry'] or '—'}")
            st.markdown(f"**Email:**  {startup['email']}")
            st.markdown(f"**Phone:**  {startup['phone'] or '—'}")
            st.markdown(f"**Website:**  {startup['website'] or '—'}")
            st.markdown(f"**Logo:**  {startup['logo_filename'] or '—'}")
            st.markdown("**About**")
            st.write(startup['description'] or '—')

            if st.button("Edit profile", type="primary", use_container_width=True):
                st.session_state["startup_editing"] = True
                st.rerun()
            st.stop()

        # --- Edit form ---
        with st.form("edit_startup"):
            name = st.text_input("Company name", value=startup["name"])
            phone = st.text_input("Phone", value=startup["phone"] or "")
            ind_idx = (
                INDUSTRY_CHOICES.index(startup["industry"])
                if startup["industry"] in INDUSTRY_CHOICES else 0
            )
            industry = st.selectbox("Industry", INDUSTRY_CHOICES, index=ind_idx)
            description = st.text_area(
                "About the company", value=startup["description"] or "", height=120,
            )
            website = st.text_input("Website", value=startup["website"] or "")
            logo_file = st.file_uploader("Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])

            ca, cb = st.columns(2)
            with ca:
                saved = st.form_submit_button("Save", type="primary", use_container_width=True)
            with cb:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state["startup_editing"] = False
            st.rerun()

        if saved:
            updates = {
                "name": name.strip(),
                "phone": phone.strip() or None,
                "industry": industry,
                "description": description.strip() or None,
                "website": website.strip() or None,
            }
            if logo_file is not None:
                updates["logo_filename"] = _save_logo(logo_file, startup["id"])
            update_startup(startup["id"], **updates)
            st.session_state["startup_editing"] = False
            st.success("Profile updated.")
            st.rerun()

        st.stop()


# =========================================================================
# Mode 2: signup form (no startup_id in session)
# =========================================================================

st.markdown("# Create your company profile")
st.caption("This is what students see when you post a role. Takes about two minutes.")

with st.form("startup_signup"):
    name = st.text_input("Company name *")
    email = st.text_input(
        "Company email *",
        help="We'll send applicant notifications here.",
    )
    phone = st.text_input("Phone")
    industry = st.selectbox("Industry", INDUSTRY_CHOICES)
    description = st.text_area("About the company", height=120)
    website = st.text_input("Website", placeholder="https://yourcompany.com")
    logo_file = st.file_uploader("Logo (PNG/JPG, optional)", type=["png", "jpg", "jpeg"])

    submitted = st.form_submit_button(
        "Create profile", type="primary", use_container_width=True,
    )

if submitted:
    if not name.strip() or not email.strip():
        st.error("Company name and email are required.")
        st.stop()

    existing = get_startup_by_email(email.strip())
    if existing:
        st.session_state["role"] = "startup"
        st.session_state["startup_id"] = existing["id"]
        st.info("Welcome back! We found your existing profile.")
        st.switch_page("pages/6_Startup_Listings.py")

    sid = create_startup(
        name=name.strip(),
        email=email.strip(),
        phone=phone.strip() or None,
        industry=industry,
        description=description.strip() or None,
        website=website.strip() or None,
    )
    if logo_file is not None:
        logo_name = _save_logo(logo_file, sid)
        update_startup(sid, logo_filename=logo_name)

    st.session_state["role"] = "startup"
    st.session_state["startup_id"] = sid

    startup_row = get_startup(sid)
    subject, body = signup_confirm_startup(startup_row)
    send_email(startup_row["email"], subject, body)

    st.success("Profile created. Welcome email sent.")
    st.switch_page("pages/6_Startup_Listings.py")
