"""
System settings and configuration models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.sql import func
from .database import Base

class SystemSetting(Base):
    """System configuration settings"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False)  # 'string', 'int', 'float', 'bool', 'json'
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # 'bot', 'ai', 'study', 'quiz', 'points', 'system'
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class APIConfig(Base):
    """API configuration and keys"""
    __tablename__ = "api_config"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(50), nullable=False)
    api_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())