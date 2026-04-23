from fastapi import APIRouter
from app.schemas.events import EventRequest
from app.schemas.adapt import AdaptRequest
from app.models.db import SessionLocal
from app.models.event import Event
from app.routers.adapt import adapt

router = APIRouter()


def aggregate_event_batch(events):
    if not events:
        return {
            "latency_delta": 0.0,
            "error_rate": 0.0,
            "attempt_burst": 0,
            "attention_drop": 0.0,
            "hint_reliance": 0.0,
            "cold_start_latency": 0.0,
            "exit_flag_ratio": 0.0,
            "reread_normalized": 0.0,
        }

    feature_rows = [e.features.dict() for e in events]
    n = len(feature_rows)

    return {
        "latency_delta": sum(x["latency_delta"] for x in feature_rows) / n,
        "error_rate": sum(x["error_rate"] for x in feature_rows) / n,
        "attempt_burst": max(x["attempt_burst"] for x in feature_rows),
        "attention_drop": sum(x["attention_drop"] for x in feature_rows) / n,
        "hint_reliance": sum(x["hint_reliance"] for x in feature_rows) / n,
        "cold_start_latency": sum(x["cold_start_latency"] for x in feature_rows) / n,
        "exit_flag_ratio": sum(x["exit_flag_ratio"] for x in feature_rows) / n,
        "reread_normalized": sum(x["reread_normalized"] for x in feature_rows) / n,
    }


@router.post("/events")
def receive_event(data: EventRequest):
    db = SessionLocal()

    try:
        for item in data.events:
            event = Event(
                student_id=data.student_id,
                content_id=data.content_id,
                latency_delta=item.features.latency_delta,
                error_rate=item.features.error_rate,
                attempt_burst=item.features.attempt_burst,
                attention_drop=item.features.attention_drop,
                hint_reliance=item.features.hint_reliance,
                cold_start_latency=item.features.cold_start_latency,
                exit_flag_ratio=item.features.exit_flag_ratio,
                reread_normalized=item.features.reread_normalized,
            )
            db.add(event)

        db.commit()

    finally:
        db.close()

    aggregated_features = aggregate_event_batch(data.events)

    adapt_input = AdaptRequest(
        student_id=data.student_id,
        content_id=data.content_id,
        features=aggregated_features
    )

    adapt_response = adapt(adapt_input)

    if hasattr(adapt_response, "dict"):
        adapt_response = adapt_response.dict()

    return {
        "stored": True,
        "aggregated_features": aggregated_features,
        "adapt": adapt_response
    }