"""
Study tracking models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base

class StudySession(Base):
    """Study session records"""
    __tablename__ = "study_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    username = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    points_earned = Column(Float, default=0.0, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class StudyGoal(Base):
    """User study goals"""
    __tablename__ = "study_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    username = Column(String(100), nullable=False)
    goal_text = Column(Text, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())