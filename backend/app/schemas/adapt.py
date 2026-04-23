from pydantic import BaseModel
from typing import List, Optional


class Features(BaseModel):
    latency_delta: float
    error_rate: float
    attempt_burst: int
    attention_drop: int
    hint_reliance: float
    cold_start_latency: float
    exit_flag_ratio: float
    reread_normalized: float

    wrong_streak: int = 0
    total_attempts: int = 0
    hints_used: int = 0
    rereads: int = 0
    avg_response_time: float = 0.0


class AdaptRequest(BaseModel):
    student_id: str
    content_id: str
    features: Features
    behavior_summary: Optional[str] = None
    disable_cache: bool = False


class Prediction(BaseModel):
    strain_level: str
    confidence: float
    trigger_adaptation: bool
    top_features: List[str]


class AdaptResponse(BaseModel):
    prediction: Prediction
    adaptation: str
    explanation_note: str