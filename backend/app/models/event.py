from sqlalchemy import Column, Integer, Float, String
from app.models.db import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String)
    content_id = Column(String)

    latency_delta = Column(Float)
    error_rate = Column(Float)
    attempt_burst = Column(Integer)
    attention_drop = Column(Integer)
    hint_reliance = Column(Float)
    cold_start_latency = Column(Float)
    exit_flag_ratio = Column(Float)
    reread_normalized = Column(Float)