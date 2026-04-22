from fastapi import APIRouter
from app.services.ml_client import predict_strain
from app.services.gpt_adapter import generate_adaptation
from app.services.retention_tracker import start_tracking

router = APIRouter()

@router.post("/adapt")
def adapt(data: dict):
    student_id = data.get("student_id")
    content_id = data.get("content_id")
    features = data.get("features", {})

    # ---- ML Prediction ----
    prediction = predict_strain(features)

    # ---- Adaptation ----
    adaptation = generate_adaptation(prediction)

    # ---- START RETENTION TRACKING ----
    # use accuracy proxy (1 - error_rate)
    error_rate = features.get("error_rate", 0)
    pre_accuracy = 1 - error_rate

    start_tracking(
        student_id=student_id,
        content_id=content_id,
        pre_accuracy=pre_accuracy
    )

    return {
        "prediction": prediction,
        "adaptation": adaptation
    }