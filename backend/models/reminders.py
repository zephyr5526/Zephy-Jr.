"""
Reminder system models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base

class Reminder(Base):
    """User reminders"""
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    username = Column(String(100), nullable=False)
    reminder_text = Column(Text, nullable=False)
    trigger_time = Column(DateTime(timezone=True), nullable=False)
    is_triggered = Column(Boolean, default=False, nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    is_cancelled = Column(Boolean, default=False, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())