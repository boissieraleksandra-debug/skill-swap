"""
seed.py — One-shot script that fills app.db with sample startups and jobs.

Run from the project root:
    python seed.py

It will:
  1) Create the database schema if needed (calls db.init_db()).
  2) Insert the 5 sample startups from data/sample_startups.json,
     skipping any that already exist (matched by email).
  3) Insert the 15 sample jobs from data/sample_jobs.json, looking up
     each startup by its email.

Re-running is safe — existing rows are not duplicated.
To reset everything: delete app.db, then run this script again.
"""

import json
from pathlib import Path

from db import (
    init_db,
    get_conn,
    create_startup,
    get_startup_by_email,
    create_job,
)

DATA_DIR = Path(__file__).parent / "data"


def load_json(name):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def seed_startups():
    for s in load_json("sample_startups.json"):
        if get_startup_by_email(s["email"]):
            continue                                        # already there
        create_startup(
            name=s["name"],
            email=s["email"],
            phone=s.get("phone"),
            industry=s.get("industry"),
            description=s.get("description"),
            website=s.get("website"),
            logo_filename=s.get("logo_filename"),
        )
        print(f"  + startup: {s['name']}")


def seed_jobs():
    # Avoid inserting jobs that share a title with an existing one — keeps
    # the seeder idempotent without needing a unique constraint on title.
    conn = get_conn()
    existing_titles = {row["title"] for row in conn.execute("SELECT title FROM jobs")}
    conn.close()

    for j in load_json("sample_jobs.json"):
        if j["title"] in existing_titles:
            continue
        startup = get_startup_by_email(j["startup_email"])
        if not startup:
            print(f"  ! skipping '{j['title']}' (startup '{j['startup_email']}' not found)")
            continue
        create_job(
            startup_id=startup["id"],
            title=j["title"],
            short_desc=j["short_desc"],
            long_desc=j["long_desc"],
            requirements=j["requirements"],
            location=j["location"],
            duration=j["duration"],
            pay_rate=j["pay_rate"],
            industry=j["industry"],
            tags=j["tags"],
            image_url=j["image_url"],
        )
        print(f"  + job: {j['title']}")


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Seeding startups...")
    seed_startups()
    print("Seeding jobs...")
    seed_jobs()
    print("Done.")
