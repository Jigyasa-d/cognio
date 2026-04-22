from fastapi import APIRouter
from app.models.db import SessionLocal
from app.models.retention import RetentionEvent

router = APIRouter()


# 👉 Student-wise analytics
@router.get("/analytics/{student_id}")
def get_student_analytics(student_id: str):
    db = SessionLocal()

    records = db.query(RetentionEvent).filter(
        RetentionEvent.student_id == student_id
    ).all()

    db.close()

    return [
        {
            "content_id": r.content_id,
            "pre_accuracy": r.pre_accuracy,
            "post_avg": r.post_avg,
            "delta": r.delta,
            "flagged": r.flagged
        }
        for r in records
    ]


# 👉 Teacher dashboard (flagged students)
@router.get("/analytics/flagged")
def get_flagged_students():
    db = SessionLocal()

    records = db.query(RetentionEvent).filter(
        RetentionEvent.flagged == True
    ).all()

    db.close()

    return [
        {
            "student_id": r.student_id,
            "content_id": r.content_id,
            "delta": r.delta
        }
        for r in records
    ]