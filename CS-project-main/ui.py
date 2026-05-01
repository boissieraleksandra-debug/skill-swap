"""
ui.py — small UI helpers reused on every page.

- load_css(): inject our custom stylesheet.
- industry_class(): map an industry name to a CSS class slug.
- sidebar(): render the role-aware sidebar — page nav (filtered to
  the current role), the Inbox panel showing sent emails (with a
  real / simulated send-mode tag), and a Log-out button.

We also load `.env` once on import so RESEND_API_KEY is visible to any
page that calls sidebar(), even if that page never imports mailer.
"""

import os
from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CSS_PATH = Path(__file__).parent / "static" / "style.css"


def load_css():
    """Inject our stylesheet into the current Streamlit page.

    Call this once near the top of every page (after st.set_page_config).
    """
    if CSS_PATH.exists():
        css = CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def industry_class(industry: str) -> str:
    """Map an industry name (e.g. 'Sustainability') to a CSS class slug."""
    if not industry:
        return ""
    known = {"marketing", "tech", "finance", "sustainability", "design"}
    slug = industry.strip().lower()
    return slug if slug in known else ""


def sidebar():
    """Render the full role-aware sidebar: nav + inbox + logout."""
    role = st.session_state.get("role")

    with st.sidebar:
        st.markdown(
            "<div class='gigly-wordmark'>gigly</div>"
            "<div class='gigly-tagline'>Students × Startups</div>",
            unsafe_allow_html=True,
        )

        if role == "student":
            st.page_link("pages/1_Profile.py",           label="Profile")
            st.page_link("pages/2_Discovery.py",         label="Discover")
            st.page_link("pages/3_Liked_Jobs.py",        label="Saved")
            st.page_link("pages/4_Student_Dashboard.py", label="Dashboard")
        elif role == "startup":
            st.page_link("pages/5_Startup_Profile.py",      label="Company")
            st.page_link("pages/6_Startup_Listings.py",     label="Listings")
            st.page_link("pages/7_Startup_Applications.py", label="Applicants")
            st.page_link("pages/8_Startup_Dashboard.py",    label="Dashboard")
        else:
            st.page_link("app.py", label="Home")

        st.divider()

        from db import list_emails
        real_mode = bool(os.getenv("RESEND_API_KEY", "").strip())
        mode_label = "Live delivery (Resend)" if real_mode else "Simulated mode"

        with st.expander("Inbox", expanded=False):
            st.caption(mode_label)
            emails = list_emails(limit=10)
            if not emails:
                st.caption("No messages yet.")
            else:
                for e in emails:
                    status = "Sent" if e["sent_ok"] else "Failed"
                    st.markdown(f"**{e['subject']}**")
                    st.caption(f"{status} · To: {e['to_email']} · {e['created_at']}")
                    with st.expander("Read", expanded=False):
                        st.text(e["body"])
                    st.divider()

        if role:
            if st.button("Log out", use_container_width=True):
                for k in ("role", "student_id", "startup_id",
                          "profile_editing", "startup_editing",
                          "expanded_job", "viewing_application_id",
                          "new_job_form_open"):
                    st.session_state.pop(k, None)
                st.switch_page("app.py")
