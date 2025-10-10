"""
Points system models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from .database import Base

class UserPoints(Base):
    """User points and statistics"""
    __tablename__ = "user_points"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=True)
    total_points = Column(Float, default=0.0, nullable=False)
    study_points = Column(Float, default=0.0, nullable=False)
    chat_points = Column(Float, default=0.0, nullable=False)
    quiz_points = Column(Float, default=0.0, nullable=False)
    bonus_points = Column(Float, default=0.0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PointsTransaction(Base):
    """Points transaction history"""
    __tablename__ = "points_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    points = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # 'earn', 'spend', 'bonus', 'penalty'
    source = Column(String(100), nullable=False)  # 'study', 'chat', 'quiz', 'admin'
    description = Column(Text, nullable=True)
    metadata = Column(JSON, default=dict, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())