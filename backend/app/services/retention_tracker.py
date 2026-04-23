import time
from app.models.retention import RetentionEvent
from app.models.db import SessionLocal

# -------- In-memory store (Redis-like simulation) -------- #
tracking_state = {}

# expire tracking after 10 minutes
TTL_SECONDS = 600


def start_tracking(student_id, content_id, pre_accuracy):
    tracking_state[(student_id, content_id)] = {
        "pre_accuracy": pre_accuracy,
        "post_scores": [],
        "created_at": time.time()
    }


def record_post_event(student_id, content_id, score):
    key = (student_id, content_id)

    if key not in tracking_state:
        return None

    data = tracking_state[key]

    # -------- TTL CHECK (simulate Redis expiry) -------- #
    if time.time() - data["created_at"] > TTL_SECONDS:
        del tracking_state[key]
        return None

    # -------- ADD SCORE -------- #
    data["post_scores"].append(score)

    if len(data["post_scores"]) == 3:
        return finalize_tracking(student_id, content_id)

    return None


def finalize_tracking(student_id, content_id):
    key = (student_id, content_id)
    data = tracking_state[key]

    pre = data["pre_accuracy"]
    post_avg = sum(data["post_scores"]) / len(data["post_scores"])
    delta = post_avg - pre

    flagged = delta < 0

    db = SessionLocal()

    event = RetentionEvent(
        student_id=student_id,
        content_id=content_id,
        pre_accuracy=pre,
        post_avg=post_avg,
        delta=delta,
        flagged=flagged
    )

    db.add(event)
    db.commit()
    db.close()

    # -------- CLEANUP -------- #
    del tracking_state[key]

    return {
        "delta": delta,
        "flagged": flagged
    }