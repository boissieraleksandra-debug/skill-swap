"""
mailer.py — sending the app's transactional emails.

Two modes, picked automatically:

1. **Real send** via Resend (https://resend.com) when RESEND_API_KEY
   is set in the environment / .env file. Resend has a free tier
   (3 000 emails/month) and a 1-line Python SDK.

2. **Simulated** when no API key is set. The email body is written
   only to the `emails_log` table; the in-app "📬 Inbox" panel inside
   ui.sidebar() shows them so we can demo without internet.

Either way every send is logged, so we can prove "the app sends emails"
in the demo regardless of which mode is active.
"""

import os

# .env support — silently skip if dotenv isn't installed yet.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from db import log_email


def send_email(to_email: str, subject: str, body: str) -> tuple[bool, str | None]:
    """Send an email. Returns (ok, error_message).

    - In real mode: calls Resend.
    - In simulated mode: just logs to the database.
    """
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("FROM_EMAIL", "onboarding@resend.dev").strip()

    # ----- Simulated mode -----
    if not api_key:
        log_email(to_email, subject, body, sent_ok=True, error=None)
        return True, None

    # ----- Real send via Resend -----
    try:
        import resend                                       # imported lazily
        resend.api_key = api_key
        # Resend wants HTML; \n -> <br> is enough for our plain-text bodies.
        html_body = body.replace("\n", "<br>\n")
        resend.Emails.send({
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        })
        log_email(to_email, subject, body, sent_ok=True, error=None)
        return True, None
    except Exception as e:                                  # noqa: BLE001
        log_email(to_email, subject, body, sent_ok=False, error=str(e))
        return False, str(e)
