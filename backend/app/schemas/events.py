from pydantic import BaseModel
from typing import List


class Features(BaseModel):
    latency_delta: float
    error_rate: float
    attempt_burst: int
    attention_drop: float
    hint_reliance: float
    cold_start_latency: float
    exit_flag_ratio: float
    reread_normalized: float


class EventItem(BaseModel):
    timestamp: float
    features: Features


class EventRequest(BaseModel):
    student_id: str
    content_id: str
    events: List[EventItem]