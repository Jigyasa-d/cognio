from fastapi import APIRouter
from app.schemas.adapt import AdaptRequest, AdaptResponse
from app.services.ml_client import predict_strain
from app.services.gpt_adapter import transform_content
from app.services.retention_tracker import start_tracking

router = APIRouter()


@router.post("/adapt", response_model=AdaptResponse)
def adapt(data: AdaptRequest):
    student_id = data.student_id
    content_id = data.content_id

    # 🔴 Convert Pydantic model → dict
    features = data.features.dict()

    # ---- ML Prediction ----
    prediction = predict_strain(features)

    # ---- LLM Adaptation ----
    adaptation = transform_content(prediction)

    # ---- Retention Tracking ----
    error_rate = features.get("error_rate", 0)
    pre_accuracy = 1 - error_rate

    start_tracking(
        student_id=student_id,
        content_id=content_id,
        pre_accuracy=pre_accuracy
    )

    return AdaptResponse(
        prediction=prediction,
        adaptation=adaptation
    )