from fastapi import APIRouter
from app.schemas.events import EventRequest
from app.models.db import SessionLocal
from app.models.event import Event
from app.services.ml_client import predict_strain

router = APIRouter()

@router.post("/events")
def receive_event(data: EventRequest):
    db = SessionLocal()

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
    db.close()

    # 🔴 ML prediction
    prediction = predict_strain({
        "latency_delta": data.features.latency_delta,
        "error_rate": data.features.error_rate,
        "attempt_burst": data.features.attempt_burst,
        "hint_reliance": data.features.hint_reliance
    })

    return {
        "stored": True,
        "prediction": prediction
    }