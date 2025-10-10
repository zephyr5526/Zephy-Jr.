"""
Bot status and configuration models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from .database import Base

class BotStatus(Base):
    """Bot status and configuration"""
    __tablename__ = "bot_status"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String(100), unique=True, index=True, nullable=False)
    is_running = Column(Boolean, default=False, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    message_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    oauth_index = Column(Integer, default=0, nullable=False)
    config = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BotConfig(Base):
    """Bot configuration settings"""
    __tablename__ = "bot_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())