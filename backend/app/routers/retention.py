from fastapi import APIRouter
from app.services.retention_tracker import record_post_event

router = APIRouter()


@router.post("/retention/event")
def retention_event(data: dict):
    student_id = data.get("student_id")
    content_id = data.get("content_id")
    score = data.get("score")

    result = record_post_event(student_id, content_id, score)

    return {
        "status": "recorded",
        "result": result  # will be None until 3 events complete
    }