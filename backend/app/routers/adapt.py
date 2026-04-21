from fastapi import APIRouter
from app.services.ml_client import predict_strain
from app.services.gpt_adapter import generate_adaptation

router = APIRouter()

@router.post("/adapt")
def adapt(data: dict):
    features = data.get("features", {})

    prediction = predict_strain(features)

    adaptation = generate_adaptation(prediction)

    return {
        "prediction": prediction,
        "adaptation": adaptation
    }