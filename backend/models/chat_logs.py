"""
Chat logs and message models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base

class ChatLog(Base):
    """Chat message logs"""
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String(100), index=True, nullable=False)
    message_id = Column(String(200), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    username = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=True)
    message_text = Column(Text, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_moderator = Column(Boolean, default=False, nullable=False)
    is_owner = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processed = Column(Boolean, default=False, nullable=False)
    response_text = Column(Text, nullable=True)
    response_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BotResponse(Base):
    """Bot response logs"""
    __tablename__ = "bot_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    stream_id = Column(String(100), index=True, nullable=False)
    chat_log_id = Column(Integer, nullable=True)  # Reference to ChatLog
    response_text = Column(Text, nullable=False)
    response_type = Column(String(50), nullable=False)  # 'command', 'mention', 'welcome', 'periodic'
    target_user = Column(String(100), nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())