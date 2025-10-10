"""
Chat management router
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.database import get_db
from models.schemas import ChatMessageRequest, ChatLogResponse, ErrorResponse
from models.chat_logs import ChatLog, BotResponse
from utils.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/send", response_model=ChatLogResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a manual chat message"""
    try:
        # Get bot runner from app state
        from main import app
        bot_runner = app.state.bot_runner
        
        # Check if bot is running for this stream
        status_data = bot_runner.get_bot_status(request.stream_id)
        if not status_data.get("is_running", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bot is not running for this stream"
            )
        
        # Import the original bot's send function
        from Chatbot_old import send_chat_message as original_send_chat_message, get_chat_id, authenticate_youtube
        
        # Get YouTube client and chat ID
        from Chatbot_old import CLIENT_SECRET_FILES
        youtube = authenticate_youtube(CLIENT_SECRET_FILES[0])
        if not youtube:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to authenticate with YouTube"
            )
        
        chat_id = get_chat_id(youtube, request.stream_id)
        if not chat_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get chat ID for stream"
            )
        
        # Send the message
        success = original_send_chat_message(
            youtube, 
            chat_id, 
            request.message, 
            request.target_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send message"
            )
        
        # Log the message
        chat_log = ChatLog(
            stream_id=request.stream_id,
            message_id=f"manual_{datetime.utcnow().timestamp()}",
            user_id="admin",
            username="Admin",
            message_text=request.message,
            is_admin=True,
            timestamp=datetime.utcnow(),
            processed=True,
            response_text=request.message,
            response_time=datetime.utcnow()
        )
        db.add(chat_log)
        db.commit()
        
        logger.info(f"📤 Manual message sent to stream {request.stream_id}: {request.message}")
        
        return ChatLogResponse(
            data=[{
                "id": chat_log.id,
                "message": request.message,
                "timestamp": chat_log.timestamp.isoformat(),
                "target_user": request.target_user
            }],
            total=1,
            page=1,
            limit=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Send message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/logs", response_model=ChatLogResponse)
async def get_chat_logs(
    stream_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat logs for a stream"""
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Query chat logs
        query = db.query(ChatLog).filter(ChatLog.stream_id == stream_id)
        total = query.count()
        
        logs = query.order_by(desc(ChatLog.timestamp)).offset(offset).limit(limit).all()
        
        # Format response data
        data = []
        for log in logs:
            data.append({
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "display_name": log.display_name,
                "message": log.message_text,
                "is_admin": log.is_admin,
                "is_moderator": log.is_moderator,
                "is_owner": log.is_owner,
                "timestamp": log.timestamp.isoformat(),
                "processed": log.processed,
                "response": log.response_text,
                "response_time": log.response_time.isoformat() if log.response_time else None
            })
        
        return ChatLogResponse(
            data=data,
            total=total,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"❌ Get chat logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/stats")
async def get_chat_stats(
    stream_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat statistics for a stream"""
    try:
        # Get basic stats
        total_messages = db.query(ChatLog).filter(ChatLog.stream_id == stream_id).count()
        admin_messages = db.query(ChatLog).filter(
            ChatLog.stream_id == stream_id,
            ChatLog.is_admin == True
        ).count()
        
        # Get recent activity (last 24 hours)
        since = datetime.utcnow() - timedelta(hours=24)
        recent_messages = db.query(ChatLog).filter(
            ChatLog.stream_id == stream_id,
            ChatLog.timestamp >= since
        ).count()
        
        # Get unique users
        unique_users = db.query(ChatLog.user_id).filter(
            ChatLog.stream_id == stream_id
        ).distinct().count()
        
        return {
            "stream_id": stream_id,
            "total_messages": total_messages,
            "admin_messages": admin_messages,
            "recent_messages_24h": recent_messages,
            "unique_users": unique_users
        }
        
    except Exception as e:
        logger.error(f"❌ Get chat stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )