from fastapi import APIRouter
from app.schemas.events import EventRequest
from app.schemas.adapt import AdaptRequest
from app.models.db import SessionLocal
from app.models.event import Event
from app.routers.adapt import adapt

router = APIRouter()


@router.post("/events")
def receive_event(data: EventRequest):
    db = SessionLocal()

    try:
        # -------- STORE EVENT IN DB -------- #
        event = Event(
            student_id=data.student_id,
            content_id=data.content_id,
            latency_delta=data.features.latency_delta,
            error_rate=data.features.error_rate,
            attempt_burst=data.features.attempt_burst,
            attention_drop=data.features.attention_drop,
            hint_reliance=data.features.hint_reliance,
            cold_start_latency=data.features.cold_start_latency,
            exit_flag_ratio=data.features.exit_flag_ratio,
            reread_normalized=data.features.reread_normalized,
        )

        db.add(event)
        db.commit()

    finally:
        db.close()

    # -------- CONVERT TO ADAPT SCHEMA -------- #
    adapt_input = AdaptRequest(
        student_id=data.student_id,
        content_id=data.content_id,
        features=data.features.dict()  # 🔥 FIX (MANDATORY)
    )

    # -------- CALL ADAPT PIPELINE -------- #
    adapt_response = adapt(adapt_input)

    # -------- SAFE SERIALIZATION -------- #
    if hasattr(adapt_response, "dict"):
        adapt_response = adapt_response.dict()

    return {
        "stored": True,
        "adapt": adapt_response
    }