from fastapi import APIRouter
from app.schemas.adapt import AdaptRequest, AdaptResponse
from app.services.ml_client import predict_strain
from app.services.gpt_adapter import transform_content
from app.services.retention_tracker import start_tracking
from app.services.cache_manager import generate_cache_key, get_from_cache, set_cache
from app.models.content_library import ContentLibrary
from app.models.db import SessionLocal

router = APIRouter()


def build_explanation_note(prediction: dict) -> str:
    features = prediction.get("top_features", [])
    if not features:
        return "Adapted based on overall performance."
    return f"Adapted due to: {', '.join(features)}."


@router.post("/adapt", response_model=AdaptResponse)
def adapt(data: AdaptRequest):
    student_id = data.student_id
    content_id = data.content_id
    features = data.features.dict()

    # ---- ML ----
    prediction = predict_strain(features)

    # ---- Explanation ----
    explanation_note = build_explanation_note(prediction)

    strain = prediction.get("strain_level", "LOW")

    # ---- CACHE CHECK ----
    cache_key = generate_cache_key(content_id, strain)
    cached = get_from_cache(cache_key)

    if cached:
        return AdaptResponse(
            prediction=prediction,
            adaptation=cached,
            explanation_note=explanation_note
        )

    # ---- GPT ----
    adaptation = transform_content(prediction, explanation_note)

    # ---- CACHE SAVE ----
    set_cache(cache_key, adaptation)

    # ---- DB SAVE ----
    db = SessionLocal()
    db.add(ContentLibrary(
        cache_key=cache_key,
        content_id=content_id,
        strain_level=strain,
        adapted_text=adaptation
    ))
    db.commit()
    db.close()

    # ---- RETENTION ----
    error_rate = features.get("error_rate", 0)
    pre_accuracy = 1 - error_rate

    start_tracking(
        student_id=student_id,
        content_id=content_id,
        pre_accuracy=pre_accuracy
    )

    return AdaptResponse(
        prediction=prediction,
        adaptation=adaptation,
        explanation_note=explanation_note
    )