from sqlalchemy import Column, Integer, String, Float, Boolean
from app.models.db import Base

class RetentionEvent(Base):
    __tablename__ = "retention_events"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String)
    content_id = Column(String)

    pre_accuracy = Column(Float)
    post_avg = Column(Float)
    delta = Column(Float)

    flagged = Column(Boolean, default=False)