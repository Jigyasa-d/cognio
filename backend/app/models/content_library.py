from sqlalchemy import Column, String, Text
from app.models.db import Base


class ContentLibrary(Base):
    __tablename__ = "content_library"

    cache_key = Column(String, primary_key=True)
    content_id = Column(String)
    strain_level = Column(String)
    adapted_text = Column(Text)