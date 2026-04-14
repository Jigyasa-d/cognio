from pydantic import BaseModel

class Features(BaseModel):
    latency_delta: float
    error_rate: float
    attempt_burst: int
    attention_drop: int
    hint_reliance: float
    cold_start_latency: float
    exit_flag_ratio: float
    reread_normalized: float

class EventRequest(BaseModel):
    student_id: str
    content_id: str
    features: Features