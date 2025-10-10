"""
Pydantic schemas for API requests and responses
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr

# Base response schema
class BaseResponse(BaseModel):
    status: str = "success"
    message: str = "Operation completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Authentication schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseResponse):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None

# Bot control schemas
class BotStatusResponse(BaseResponse):
    data: Dict[str, Any]

class BotStartRequest(BaseModel):
    stream_id: str
    video_url: Optional[str] = None

class BotStopRequest(BaseModel):
    stream_id: str

# Chat schemas
class ChatMessageRequest(BaseModel):
    stream_id: str
    message: str
    target_user: Optional[str] = None

class ChatLogResponse(BaseResponse):
    data: List[Dict[str, Any]]
    total: int
    page: int
    limit: int

# AI schemas
class AIRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=200, ge=1, le=1000)

class AIResponse(BaseResponse):
    data: Dict[str, Any]

# Study schemas
class StudySessionRequest(BaseModel):
    stream_id: str
    user_id: str
    username: str
    action: str  # 'start' or 'stop'

class StudySessionResponse(BaseResponse):
    data: Dict[str, Any]

class StudyGoalRequest(BaseModel):
    stream_id: str
    user_id: str
    username: str
    goal_text: str

class StudyGoalResponse(BaseResponse):
    data: Dict[str, Any]

# Reminder schemas
class ReminderRequest(BaseModel):
    stream_id: str
    user_id: str
    username: str
    reminder_text: str
    delay_minutes: int = Field(ge=1, le=1440)  # 1 minute to 24 hours

class ReminderResponse(BaseResponse):
    data: Dict[str, Any]

# Quiz schemas
class QuizStartRequest(BaseModel):
    stream_id: str
    user_id: str
    username: str

class QuizAnswerRequest(BaseModel):
    stream_id: str
    user_id: str
    username: str
    answer: str

class QuizResponse(BaseResponse):
    data: Dict[str, Any]

# Points schemas
class PointsResponse(BaseResponse):
    data: List[Dict[str, Any]]

class PointsTransactionRequest(BaseModel):
    user_id: str
    points: float
    transaction_type: str
    source: str
    description: Optional[str] = None

# System settings schemas
class SystemSettingRequest(BaseModel):
    key: str
    value: Union[str, int, float, bool, Dict[str, Any]]
    description: Optional[str] = None

class SystemSettingResponse(BaseResponse):
    data: Dict[str, Any]

# WebSocket schemas
class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Error schemas
class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)