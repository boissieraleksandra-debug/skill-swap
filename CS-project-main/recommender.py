"""
recommender.py — TF-IDF + cosine similarity job recommender.

This is the project's "machine learning" component. It is a real,
textbook content-based recommender, but only ~70 lines so the team
can read and explain every step in the demo video.

How it works
------------
1. Build the corpus = every currently-open job as a single text:
       title + long_desc + tags + industry
2. Build the student profile text:
       interests + education + availability
   then append:
     * the text of every job the student LIKED (full weight)
     * the text of every job the student CLICKED (one repeat = soft signal)
3. Fit a TF-IDF vectorizer jointly on jobs + student so they share
   one vocabulary; transform everything.
4. Penalize disliked jobs by subtracting 0.3 × the mean disliked
   vector from the student vector (then clip to ≥ 0).
5. Compute cosine similarity between the (penalized) student vector
   and every candidate job; sort jobs by score, descending.
6. Return the top N along with:
     * an integer match percentage (clipped to 1..99 so the UI
       never shows a fake-looking 0% or 100%)
     * up to 2 "why this matches" terms = the highest joint TF-IDF
       weights between the original student vector and the job.

Each refresh re-runs this from scratch, which is what "the app learns"
looks like in the demo: like 3 marketing jobs, refresh, watch the
top of the feed lean marketing.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from db import (
    list_open_jobs,
    list_swipes,
    get_student,
    get_job,
)


def _job_text(job):
    return " ".join([
        job["title"]    or "",
        job["long_desc"] or "",
        job["tags"]      or "",
        job["industry"]  or "",
    ])


def _student_text(student):
    return " ".join([
        student["interests"]    or "",
        student["education"]    or "",
        student["availability"] or "",
    ])


def recommend_jobs(student_id: int, max_results: int = 8):
    """Return [(job, match_pct, why_terms), ...] sorted by predicted match.

    `match_pct` is an int in 1..99. `why_terms` is a list of up to 2
    short strings used by the UI as a "Matches your: …" caption.
    Already-liked / disliked jobs are filtered out.
    """
    student = get_student(student_id)
    if not student:
        return []

    swipes = list_swipes(student_id)
    decided_ids = {s["job_id"] for s in swipes if s["action"] in ("like", "dislike")}

    candidates = [j for j in list_open_jobs() if j["id"] not in decided_ids]
    if not candidates:
        return []

    job_texts = [_job_text(j) for j in candidates]

    # Build the student profile text + boost from interaction history.
    parts = [_student_text(student)]
    liked_ids    = [s["job_id"] for s in swipes if s["action"] == "like"]
    clicked_ids  = [s["job_id"] for s in swipes if s["action"] == "click"]
    disliked_ids = [s["job_id"] for s in swipes if s["action"] == "dislike"]
    for jid in liked_ids:
        j = get_job(jid)
        if j:
            parts.append(_job_text(j))                      # full weight
    for jid in clicked_ids:
        j = get_job(jid)
        if j:
            parts.append(_job_text(j))                      # one repeat = soft signal
    student_text = " ".join(parts).strip()

    # Cold-start guard: brand-new student with no interests filled in
    # and no swipes yet → just show newest-first with a neutral score.
    if not student_text:
        return [(j, 50, []) for j in candidates[:max_results]]

    # Fit TF-IDF jointly so jobs and student share one vocabulary.
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        token_pattern=r"\b[a-zA-Z][a-zA-Z]+\b",
        max_features=2000,
    )
    matrix = vectorizer.fit_transform(job_texts + [student_text])
    vocab = vectorizer.get_feature_names_out()
    job_matrix    = matrix[: len(job_texts)]
    student_vec   = np.asarray(matrix[len(job_texts):].todense())   # (1, n) dense

    # Push down jobs similar to the student's dislikes.
    if disliked_ids:
        disliked_texts = []
        for jid in disliked_ids:
            j = get_job(jid)
            if j:
                disliked_texts.append(_job_text(j))
        if disliked_texts:
            disliked = np.asarray(
                vectorizer.transform(disliked_texts).mean(axis=0)
            )
            student_vec = np.maximum(student_vec - 0.3 * disliked, 0)

    # Score every candidate against the (penalized) student vector.
    scores = cosine_similarity(student_vec, job_matrix)[0]
    order = np.argsort(scores)[::-1][:max_results]

    # The "why" terms use the *original* (pre-penalty) student vector
    # so we explain matches on the basis of positive interest only.
    student_vec_for_why = (
        np.asarray(matrix[len(job_texts):].todense()).ravel()
    )

    results = []
    for idx in order:
        pct = int(round(float(scores[idx]) * 100))
        pct = max(1, min(99, pct))                          # never a flat 0 or 100
        job_vec = np.asarray(job_matrix[idx].todense()).ravel()
        overlap = student_vec_for_why * job_vec
        why = []
        if overlap.max() > 0:
            top2 = np.argsort(overlap)[::-1][:2]
            why = [vocab[i] for i in top2 if overlap[i] > 0]
        results.append((candidates[idx], pct, why))

    return results
