from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ml.serve.predictor import CognioPredictor


app = FastAPI(title="Cognio ML Service", version="2.0.0")
predictor = None


class FeaturePayload(BaseModel):
    latency_delta: float = 0.0
    error_rate: float = 0.0
    attempt_burst: float = 0.0
    attention_drop: float = 0.0
    hint_reliance: float = 0.0
    cold_start_latency: float = 0.0
    exit_flag_ratio: float = 0.0
    reread_normalized: float = 0.0


class PredictRequest(BaseModel):
    student_id: str = Field(..., examples=["STU_001"])
    content_id: str = Field(..., examples=["UNIT_3_LESSON_7"])
    features: FeaturePayload


@app.on_event("startup")
def startup_event():
    global predictor
    predictor = CognioPredictor()


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": predictor is not None}


@app.post("/ml/predict")
def ml_predict(payload: PredictRequest):
    result = predictor.predict(payload.features.model_dump())
    return {
        "student_id": payload.student_id,
        "content_id": payload.content_id,
        **result,
    }