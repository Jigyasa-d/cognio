from collections import defaultdict
from app.models.retention import RetentionEvent
from app.models.db import SessionLocal

# in-memory tracking (acts like Redis for now)
tracking_state = defaultdict(dict)


def start_tracking(student_id, content_id, pre_accuracy):
    tracking_state[(student_id, content_id)] = {
        "pre_accuracy": pre_accuracy,
        "post_scores": []
    }


def record_post_event(student_id, content_id, score):
    key = (student_id, content_id)

    if key not in tracking_state:
        return None

    tracking_state[key]["post_scores"].append(score)

    if len(tracking_state[key]["post_scores"]) == 3:
        return finalize_tracking(student_id, content_id)

    return None


def finalize_tracking(student_id, content_id):
    key = (student_id, content_id)
    data = tracking_state[key]

    pre = data["pre_accuracy"]
    post_avg = sum(data["post_scores"]) / 3
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

    del tracking_state[key]

    return {
        "delta": delta,
        "flagged": flagged
    }