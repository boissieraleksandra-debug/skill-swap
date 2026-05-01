# Student ↔ Startup Matching App

A mobile-style web app that connects students with short-term startup
opportunities (jobs, internships, projects). Built as a CS group project
by 5 students using **Streamlit** and **Python**.

## What it does

- **Students** create a profile, browse a personalized job feed, like or
  dislike jobs (which trains the recommender), apply with one click, and
  track application status.
- **Startups** create a company profile, post job listings, review
  applicants, and accept or decline them. After acceptance the
  conversation moves to email — the student receives the startup's
  contact info directly.

## Quick start

```bash
pip install -r requirements.txt
python seed.py            # creates app.db + loads 5 startups, 15 jobs
streamlit run app.py
```

The app opens at <http://localhost:8501>.

## How the teacher's requirements are met

| Requirement | Implementation |
|---|---|
| Solves a problem | Two-sided student↔startup match for short gigs |
| Is an app | Streamlit multi-page web app |
| API / DB / external data | SQLite database (`app.db`), Resend email API, jobs loaded from `data/sample_jobs.json` |
| Visualization | Plotly donut + bar charts on the dashboards |
| Machine learning | TF-IDF + cosine similarity recommender that learns from like/dislike history |
| Documented code | Inline comments + docstrings; this README; `CONTRIBUTORS.md` |
| Contribution matrix | See [CONTRIBUTORS.md](CONTRIBUTORS.md) |

## Tech stack

- **Streamlit** — UI, routing, state. One framework for the whole app.
- **SQLite** — single-file database (`app.db`), zero setup.
- **scikit-learn** — TF-IDF + cosine similarity for the recommender.
- **Plotly** — interactive charts.
- **Resend** — transactional email API (free tier). Falls back to a
  simulated in-app inbox if no API key is set.

## Project layout

```
app.py                       Landing page (role picker)
pages/                       Streamlit auto-discovers these
  1_Profile.py               Student profile (signup / edit)
  2_Discovery.py             Job feed
  3_Liked_Jobs.py            Saved jobs + apply
  4_Student_Dashboard.py     Application status + charts
  5_Startup_Profile.py
  6_Startup_Listings.py
  7_Startup_Applications.py
  8_Startup_Dashboard.py
db.py                        SQLite layer (all CRUD lives here)
recommender.py               TF-IDF + cosine recommender
mailer.py                    Email sending (real or simulated)
templates.py                 Email body templates
ui.py                        Small UI helpers (CSS loader, inbox panel)
seed.py                      One-shot DB seeder
data/                        Sample startups + jobs (JSON)
static/style.css             Custom CSS (mobile-style cards)
.streamlit/config.toml       Theme + layout
```

## Configuration

Copy `.env.example` to `.env`. If you want real email sending, sign up
at [resend.com](https://resend.com) (free), get an API key, and paste
it into `.env`. If you leave `RESEND_API_KEY` empty, the app simulates
emails: every send is logged to the database and shown in a "📬 Inbox"
expander on every page. This is what to demo if Wi-Fi is unreliable on
presentation day.

## How the recommender works

The "machine learning" in this project is a **TF-IDF + cosine similarity**
content-based recommender, ~70 lines in [recommender.py](recommender.py):

1. Every open job is turned into a text bag of words: `title + long
   description + tags + industry`.
2. The student is turned into a similar text bag: `interests +
   education + availability`, plus the text of every job they've
   liked (full weight) and every job they've clicked Details on
   (half weight, one repeat).
3. We fit a `TfidfVectorizer` on the union of both, giving each
   word a TF-IDF weight in a shared vocabulary.
4. We subtract `0.3 ×` the mean of the disliked-job vectors from the
   student vector, so jobs similar to past dislikes get pushed down.
5. Cosine similarity between the student vector and every job vector
   produces a score in `[0, 1]`. We sort jobs descending and clip the
   percentage shown on each card to `1..99` so the UI never displays
   a fake-looking 0% or 100%.
6. The "Matches your: …" line under each card is computed on the
   spot: the two TF-IDF terms with the highest joint weight between
   the student and the job.

This is a real, textbook ML algorithm — not a deep network, but the
brief asked for "the app learns" and this satisfies it. Every refresh
re-runs the algorithm against the latest swipe history, which is what
"online learning" looks like in the demo.

## Reset the database

```bash
rm app.db && python seed.py
```

## Deployment

Push the repo to GitHub, then connect it at
<https://share.streamlit.io>. Add `RESEND_API_KEY` and `FROM_EMAIL` as
secrets in the Streamlit Cloud dashboard. The app gets a public URL like
`https://your-team.streamlit.app`.
