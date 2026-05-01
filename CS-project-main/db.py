"""
db.py — SQLite database layer for the Student↔Startup matching app.

This module is the ONLY place that talks to the database. Every other file
calls helper functions from here so we never have raw SQL spread across
the codebase. That keeps the rest of the app readable for the team.

Usage:
    from db import init_db, get_conn, create_student, list_open_jobs, ...
    init_db()                  # safe to call at app start; idempotent
"""

import sqlite3
from pathlib import Path

# The database is a single file in the project root. Easy to back up,
# easy to delete and re-seed for the demo.
DB_PATH = Path(__file__).parent / "app.db"


def get_conn():
    """Return a SQLite connection. Rows are accessible by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row     # row["name"] instead of row[0]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist. Safe to call multiple times."""
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL,
        email         TEXT NOT NULL UNIQUE,
        linkedin      TEXT,
        cv_filename   TEXT,
        education     TEXT,
        interests     TEXT,
        availability  TEXT,
        created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS startups (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        name           TEXT NOT NULL,
        email          TEXT NOT NULL UNIQUE,
        phone          TEXT,
        industry       TEXT,
        description    TEXT,
        website        TEXT,
        logo_filename  TEXT,
        created_at     TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        startup_id   INTEGER NOT NULL REFERENCES startups(id) ON DELETE CASCADE,
        title        TEXT NOT NULL,
        short_desc   TEXT,
        long_desc    TEXT,
        requirements TEXT,
        location     TEXT,
        duration     TEXT,
        pay_rate     TEXT,
        industry     TEXT,
        tags         TEXT,
        image_url    TEXT,
        status       TEXT NOT NULL DEFAULT 'open'
                     CHECK (status IN ('open','in_progress','done')),
        created_at   TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS swipes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        job_id      INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        action      TEXT NOT NULL CHECK (action IN ('like','dislike','click')),
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS applications (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
        job_id      INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
        status      TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','accepted','declined','completed')),
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        decided_at  TEXT,
        UNIQUE(student_id, job_id)
    );

    CREATE TABLE IF NOT EXISTS emails_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        to_email    TEXT NOT NULL,
        subject     TEXT NOT NULL,
        body        TEXT NOT NULL,
        sent_ok     INTEGER NOT NULL DEFAULT 0,
        error       TEXT,
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_swipes_student ON swipes(student_id);
    CREATE INDEX IF NOT EXISTS idx_apps_student  ON applications(student_id);
    CREATE INDEX IF NOT EXISTS idx_apps_job      ON applications(job_id);
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Student helpers
# ---------------------------------------------------------------------------

def create_student(name, email, linkedin, cv_filename, education, interests, availability):
    """Insert a new student. Returns the new student id."""
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO students
                  (name, email, linkedin, cv_filename, education, interests, availability)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (name, email, linkedin, cv_filename, education, interests, availability),
    )
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def update_student(student_id, **fields):
    """Update any subset of student columns by keyword. Quietly no-ops if empty."""
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [student_id]
    conn = get_conn()
    conn.execute(f"UPDATE students SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_student_by_email(email):
    conn = get_conn()
    row = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_student(student_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    return row


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------

def create_startup(name, email, phone, industry, description, website, logo_filename=None):
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO startups
                  (name, email, phone, industry, description, website, logo_filename)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (name, email, phone, industry, description, website, logo_filename),
    )
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def update_startup(startup_id, **fields):
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [startup_id]
    conn = get_conn()
    conn.execute(f"UPDATE startups SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_startup_by_email(email):
    conn = get_conn()
    row = conn.execute("SELECT * FROM startups WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_startup(startup_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM startups WHERE id = ?", (startup_id,)).fetchone()
    conn.close()
    return row


# ---------------------------------------------------------------------------
# Job helpers
# ---------------------------------------------------------------------------

def create_job(startup_id, title, short_desc, long_desc, requirements,
               location, duration, pay_rate, industry, tags, image_url):
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO jobs
                  (startup_id, title, short_desc, long_desc, requirements,
                   location, duration, pay_rate, industry, tags, image_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (startup_id, title, short_desc, long_desc, requirements,
         location, duration, pay_rate, industry, tags, image_url),
    )
    conn.commit()
    jid = cur.lastrowid
    conn.close()
    return jid


def update_job(job_id, **fields):
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [job_id]
    conn = get_conn()
    conn.execute(f"UPDATE jobs SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def list_open_jobs():
    """All currently-open jobs joined with their startup info."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT j.*, s.name AS startup_name, s.email AS startup_email,
                  s.phone AS startup_phone
           FROM jobs j JOIN startups s ON j.startup_id = s.id
           WHERE j.status = 'open'
           ORDER BY j.created_at DESC"""
    ).fetchall()
    conn.close()
    return rows


def list_jobs_for_startup(startup_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM jobs WHERE startup_id = ? ORDER BY created_at DESC",
        (startup_id,),
    ).fetchall()
    conn.close()
    return rows


def get_job(job_id):
    conn = get_conn()
    row = conn.execute(
        """SELECT j.*, s.name AS startup_name, s.email AS startup_email,
                  s.phone AS startup_phone
           FROM jobs j JOIN startups s ON j.startup_id = s.id
           WHERE j.id = ?""",
        (job_id,),
    ).fetchone()
    conn.close()
    return row


# ---------------------------------------------------------------------------
# Swipe + application helpers
# ---------------------------------------------------------------------------

def record_swipe(student_id, job_id, action):
    """action is one of 'like', 'dislike', 'click'."""
    assert action in ("like", "dislike", "click")
    conn = get_conn()
    conn.execute(
        "INSERT INTO swipes (student_id, job_id, action) VALUES (?, ?, ?)",
        (student_id, job_id, action),
    )
    conn.commit()
    conn.close()


def list_swipes(student_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM swipes WHERE student_id = ? ORDER BY created_at DESC",
        (student_id,),
    ).fetchall()
    conn.close()
    return rows


def list_liked_jobs(student_id):
    """Jobs the student liked, with startup info and an already_applied flag."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT j.*, s.name AS startup_name,
                  EXISTS(SELECT 1 FROM applications a
                         WHERE a.student_id = ? AND a.job_id = j.id) AS already_applied
           FROM swipes sw
           JOIN jobs j     ON sw.job_id = j.id
           JOIN startups s ON j.startup_id = s.id
           WHERE sw.student_id = ? AND sw.action = 'like'
           GROUP BY j.id
           ORDER BY MAX(sw.created_at) DESC""",
        (student_id, student_id),
    ).fetchall()
    conn.close()
    return rows


def create_application(student_id, job_id):
    """Insert a pending application; returns id or None if it already exists."""
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO applications (student_id, job_id) VALUES (?, ?)",
            (student_id, job_id),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def list_applications_for_student(student_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT a.*, j.title AS job_title, j.industry,
                  s.name AS startup_name, s.email AS startup_email,
                  s.phone AS startup_phone
           FROM applications a
           JOIN jobs j     ON a.job_id = j.id
           JOIN startups s ON j.startup_id = s.id
           WHERE a.student_id = ?
           ORDER BY a.created_at DESC""",
        (student_id,),
    ).fetchall()
    conn.close()
    return rows


def list_applications_for_startup(startup_id):
    """All applications across every job this startup has posted."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT a.*, j.title AS job_title, j.industry,
                  st.name AS student_name, st.email AS student_email,
                  st.linkedin, st.education, st.interests, st.availability,
                  st.cv_filename
           FROM applications a
           JOIN jobs j      ON a.job_id = j.id
           JOIN students st ON a.student_id = st.id
           WHERE j.startup_id = ?
           ORDER BY a.created_at DESC""",
        (startup_id,),
    ).fetchall()
    conn.close()
    return rows


def list_applications_for_job(job_id):
    conn = get_conn()
    rows = conn.execute(
        """SELECT a.*, st.name AS student_name, st.email AS student_email,
                  st.linkedin, st.education, st.interests, st.availability,
                  st.cv_filename
           FROM applications a
           JOIN students st ON a.student_id = st.id
           WHERE a.job_id = ?
           ORDER BY a.created_at DESC""",
        (job_id,),
    ).fetchall()
    conn.close()
    return rows


def get_application(app_id):
    conn = get_conn()
    row = conn.execute(
        """SELECT a.*, j.title AS job_title, j.industry,
                  st.name AS student_name, st.email AS student_email,
                  st.linkedin, st.education, st.interests, st.availability,
                  st.cv_filename,
                  s.name AS startup_name, s.email AS startup_email,
                  s.phone AS startup_phone
           FROM applications a
           JOIN jobs j      ON a.job_id = j.id
           JOIN students st ON a.student_id = st.id
           JOIN startups s  ON j.startup_id = s.id
           WHERE a.id = ?""",
        (app_id,),
    ).fetchone()
    conn.close()
    return row


def update_application_status(app_id, new_status):
    assert new_status in ("pending", "accepted", "declined", "completed")
    conn = get_conn()
    conn.execute(
        """UPDATE applications
           SET status = ?, decided_at = datetime('now')
           WHERE id = ?""",
        (new_status, app_id),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Email-log helpers (used by mailer.py)
# ---------------------------------------------------------------------------

def log_email(to_email, subject, body, sent_ok, error=None):
    conn = get_conn()
    conn.execute(
        """INSERT INTO emails_log (to_email, subject, body, sent_ok, error)
           VALUES (?, ?, ?, ?, ?)""",
        (to_email, subject, body, 1 if sent_ok else 0, error),
    )
    conn.commit()
    conn.close()


def list_emails(limit=20):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM emails_log ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows
