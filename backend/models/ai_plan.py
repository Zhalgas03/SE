# models/ai_plan.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from db import Base

class TripAIPlan(Base):
    __tablename__ = "trip_ai_plans"

    id = Column(Integer, primary_key=True, index=True)
    input_message = Column(Text, nullable=False)
    ai_reply = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
