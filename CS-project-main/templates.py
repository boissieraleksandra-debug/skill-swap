"""
templates.py — content of every email the app sends.

Each function returns a (subject, body) tuple. Bodies are plain text;
mailer.py converts \\n to <br> when sending real HTML emails.

Inputs are sqlite3.Row objects (or any dict-like). We use `row["x"] or default`
to handle NULL fields gracefully — sqlite3.Row doesn't support .get().
"""

APP_NAME = "gigly"


def signup_confirm_student(student):
    subject = f"Welcome to {APP_NAME}"
    body = f"""Hi {student['name']},

Welcome to {APP_NAME}. Your student profile is ready.

Next step: open Discover and start saving the gigs that catch your
eye. The more you interact, the sharper your recommendations get.

— The {APP_NAME} team"""
    return subject, body


def signup_confirm_startup(startup):
    subject = f"Your {APP_NAME} company profile is live"
    body = f"""Hi {startup['name']} team,

Your company profile is set up on {APP_NAME}.

You can post your first job from the Listings page.
We'll email you the moment a student applies.

— The {APP_NAME} team"""
    return subject, body


def application_confirm_student(student, job, startup):
    subject = f"You applied for {job['title']} at {startup['name']}"
    body = f"""Hi {student['name']},

Your application was sent to {startup['name']}.
We'll email you again the moment they decide.

  Role:     {job['title']}
  Location: {job['location']}
  Duration: {job['duration']}
  Pay:      {job['pay_rate']}

— The {APP_NAME} team"""
    return subject, body


def application_notify_startup(student, job, startup):
    subject = f"New applicant for {job['title']}"
    body = f"""Hi {startup['name']} team,

A new student just applied for "{job['title']}".

  Name:         {student['name']}
  Email:        {student['email']}
  LinkedIn:     {student['linkedin'] or '—'}
  Education:    {student['education'] or '—'}
  Interests:    {student['interests'] or '—'}
  Availability: {student['availability'] or '—'}
  CV:           {student['cv_filename'] or '—'}

Open the Applicants page in {APP_NAME} to accept or decline.

— The {APP_NAME} team"""
    return subject, body


def acceptance_email(student, job, startup):
    subject = f"You're in — {job['title']} at {startup['name']}"
    body = f"""Hi {student['name']},

Great news — {startup['name']} accepted your application for
"{job['title']}". You can reach the team directly:

  Email:   {startup['email']}
  Phone:   {startup['phone'] or 'on request'}
  Website: {startup['website'] or '—'}

Suggested next step: send a short intro and propose 2-3 time slots
for an intro call.

Good luck.

— The {APP_NAME} team"""
    return subject, body


def rejection_email(student, job, startup):
    subject = f"Update on your {job['title']} application"
    body = f"""Hi {student['name']},

Thanks for applying for "{job['title']}" at {startup['name']}.
After careful consideration, the team decided to move forward
with other candidates this time.

Don't take it personally — startups often have very specific
needs for short engagements. Plenty more roles in your feed.

— The {APP_NAME} team"""
    return subject, body


def job_listed_confirm(startup, job):
    subject = f"Your listing '{job['title']}' is live"
    body = f"""Hi {startup['name']} team,

Your job listing is now visible to students:

  {job['title']}
  {job['location']} — {job['duration']}
  Pay: {job['pay_rate']}

You'll get an email each time a student applies.

— The {APP_NAME} team"""
    return subject, body
