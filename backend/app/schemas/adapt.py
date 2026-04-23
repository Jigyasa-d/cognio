from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ml_client import predict_strain
from app.services.gpt_adapter import transform_content

router = APIRouter()


class AdaptRequest(BaseModel):
    student_id: str
    content_id: str
    features: dict


@router.post("/adapt")
def adapt(req: AdaptRequest):
    prediction = predict_strain(
        student_id=req.student_id,
        content_id=req.content_id,
        features=req.features,
    )

    top_features = prediction.get("top_features", [])
    explanation_note = f"Adapted due to: {', '.join(top_features)}"

    adaptation = transform_content(prediction, explanation_note)

    return {
        "prediction": prediction,
        "explanation_note": explanation_note,
        "adaptation": adaptation,
    }