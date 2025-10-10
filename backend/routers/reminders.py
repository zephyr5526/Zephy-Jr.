"""
Reminders router
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.database import get_db
from models.schemas import ReminderRequest, ReminderResponse
from models.reminders import Reminder
from utils.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/add", response_model=ReminderResponse)
async def add_reminder(
    request: ReminderRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a reminder for a user"""
    try:
        # Calculate trigger time
        trigger_time = datetime.utcnow() + timedelta(minutes=request.delay_minutes)
        
        # Create reminder
        reminder = Reminder(
            stream_id=request.stream_id,
            user_id=request.user_id,
            username=request.username,
            reminder_text=request.reminder_text,
            trigger_time=trigger_time
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        
        logger.info(f"⏰ Reminder added for {request.username}: {request.reminder_text} in {request.delay_minutes} minutes")
        
        return ReminderResponse(
            data={
                "reminder_id": reminder.id,
                "user_id": request.user_id,
                "username": request.username,
                "reminder_text": request.reminder_text,
                "trigger_time": reminder.trigger_time.isoformat(),
                "delay_minutes": request.delay_minutes
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Add reminder error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/list")
async def list_reminders(
    stream_id: str,
    user_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List reminders for a stream or user"""
    try:
        query = db.query(Reminder).filter(Reminder.stream_id == stream_id)
        
        if user_id:
            query = query.filter(Reminder.user_id == user_id)
        
        reminders = query.order_by(desc(Reminder.trigger_time)).all()
        
        data = []
        for reminder in reminders:
            data.append({
                "id": reminder.id,
                "user_id": reminder.user_id,
                "username": reminder.username,
                "reminder_text": reminder.reminder_text,
                "trigger_time": reminder.trigger_time.isoformat(),
                "is_triggered": reminder.is_triggered,
                "is_cancelled": reminder.is_cancelled,
                "created_at": reminder.created_at.isoformat()
            })
        
        return {
            "stream_id": stream_id,
            "reminders": data,
            "total": len(data)
        }
        
    except Exception as e:
        logger.error(f"❌ List reminders error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/cancel/{reminder_id}")
async def cancel_reminder(
    reminder_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a reminder"""
    try:
        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )
        
        if reminder.is_triggered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel a triggered reminder"
            )
        
        if reminder.is_cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reminder is already cancelled"
            )
        
        reminder.is_cancelled = True
        reminder.cancelled_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"❌ Reminder {reminder_id} cancelled for {reminder.username}")
        
        return {
            "message": "Reminder cancelled successfully",
            "reminder_id": reminder_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Cancel reminder error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/stats")
async def get_reminder_stats(
    stream_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get reminder statistics for a stream"""
    try:
        # Get basic stats
        total_reminders = db.query(Reminder).filter(Reminder.stream_id == stream_id).count()
        triggered_reminders = db.query(Reminder).filter(
            Reminder.stream_id == stream_id,
            Reminder.is_triggered == True
        ).count()
        cancelled_reminders = db.query(Reminder).filter(
            Reminder.stream_id == stream_id,
            Reminder.is_cancelled == True
        ).count()
        pending_reminders = db.query(Reminder).filter(
            Reminder.stream_id == stream_id,
            Reminder.is_triggered == False,
            Reminder.is_cancelled == False
        ).count()
        
        return {
            "stream_id": stream_id,
            "total_reminders": total_reminders,
            "triggered_reminders": triggered_reminders,
            "cancelled_reminders": cancelled_reminders,
            "pending_reminders": pending_reminders
        }
        
    except Exception as e:
        logger.error(f"❌ Get reminder stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )