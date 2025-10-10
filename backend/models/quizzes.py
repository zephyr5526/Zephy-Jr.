"""
Quiz system models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.sql import func
from .database import Base

class Quiz(Base):
    """Quiz questions and sessions"""
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String(100), index=True, nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # List of options
    correct_answer = Column(String(200), nullable=False)
    explanation = Column(Text, nullable=True)
    points_reward = Column(Float, default=10.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QuizParticipation(Base):
    """Quiz participation records"""
    __tablename__ = "quiz_participations"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, nullable=False)
    stream_id = Column(String(100), index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    username = Column(String(100), nullable=False)
    answer = Column(String(200), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    points_earned = Column(Float, default=0.0, nullable=False)
    response_time_seconds = Column(Float, nullable=True)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())