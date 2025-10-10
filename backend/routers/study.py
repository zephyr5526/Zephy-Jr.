"""
Study tracking router
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models.database import get_db
from models.schemas import StudySessionRequest, StudySessionResponse, StudyGoalRequest, StudyGoalResponse
from models.study_sessions import StudySession, StudyGoal
from utils.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/start", response_model=StudySessionResponse)
async def start_study_session(
    request: StudySessionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a study session"""
    try:
        if request.action != "start":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Use 'start' to begin a session."
            )
        
        # Check if user already has an active session
        active_session = db.query(StudySession).filter(
            StudySession.stream_id == request.stream_id,
            StudySession.user_id == request.user_id,
            StudySession.is_active == True
        ).first()
        
        if active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active study session"
            )
        
        # Create new session
        session = StudySession(
            stream_id=request.stream_id,
            user_id=request.user_id,
            username=request.username,
            start_time=datetime.utcnow(),
            is_active=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"📚 Study session started for {request.username} in stream {request.stream_id}")
        
        return StudySessionResponse(
            data={
                "session_id": session.id,
                "user_id": request.user_id,
                "username": request.username,
                "start_time": session.start_time.isoformat(),
                "is_active": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Start study session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/stop", response_model=StudySessionResponse)
async def stop_study_session(
    request: StudySessionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop a study session"""
    try:
        if request.action != "stop":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Use 'stop' to end a session."
            )
        
        # Find active session
        session = db.query(StudySession).filter(
            StudySession.stream_id == request.stream_id,
            StudySession.user_id == request.user_id,
            StudySession.is_active == True
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active study session found"
            )
        
        # Calculate duration and points
        end_time = datetime.utcnow()
        duration_seconds = (end_time - session.start_time).total_seconds()
        points_earned = min(duration_seconds / 60, 100)  # 1 point per minute, max 100
        
        # Update session
        session.end_time = end_time
        session.duration_seconds = duration_seconds
        session.points_earned = points_earned
        session.is_active = False
        db.commit()
        
        logger.info(f"📚 Study session ended for {request.username}: {duration_seconds:.0f}s, {points_earned:.1f} points")
        
        return StudySessionResponse(
            data={
                "session_id": session.id,
                "user_id": request.user_id,
                "username": request.username,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat(),
                "duration_seconds": duration_seconds,
                "points_earned": points_earned,
                "is_active": False
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Stop study session error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/leaderboard")
async def get_study_leaderboard(
    stream_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get study leaderboard for a stream"""
    try:
        # Get leaderboard data
        leaderboard = db.query(
            StudySession.username,
            func.sum(StudySession.duration_seconds).label('total_duration'),
            func.sum(StudySession.points_earned).label('total_points'),
            func.count(StudySession.id).label('session_count')
        ).filter(
            StudySession.stream_id == stream_id,
            StudySession.is_active == False
        ).group_by(StudySession.username).order_by(
            func.sum(StudySession.duration_seconds).desc()
        ).limit(limit).all()
        
        data = []
        for i, (username, duration, points, sessions) in enumerate(leaderboard, 1):
            data.append({
                "rank": i,
                "username": username,
                "total_duration": duration,
                "total_points": points,
                "session_count": sessions,
                "avg_duration": duration / sessions if sessions > 0 else 0
            })
        
        return {
            "stream_id": stream_id,
            "leaderboard": data,
            "total_participants": len(data)
        }
        
    except Exception as e:
        logger.error(f"❌ Get leaderboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/goal", response_model=StudyGoalResponse)
async def set_study_goal(
    request: StudyGoalRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a study goal for a user"""
    try:
        # Check if user already has an active goal
        existing_goal = db.query(StudyGoal).filter(
            StudyGoal.stream_id == request.stream_id,
            StudyGoal.user_id == request.user_id,
            StudyGoal.is_completed == False
        ).first()
        
        if existing_goal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active goal"
            )
        
        # Create new goal
        goal = StudyGoal(
            stream_id=request.stream_id,
            user_id=request.user_id,
            username=request.username,
            goal_text=request.goal_text
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        logger.info(f"🎯 Study goal set for {request.username}: {request.goal_text}")
        
        return StudyGoalResponse(
            data={
                "goal_id": goal.id,
                "user_id": request.user_id,
                "username": request.username,
                "goal_text": request.goal_text,
                "is_completed": False,
                "created_at": goal.created_at.isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Set study goal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/stats")
async def get_study_stats(
    stream_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get study statistics for a stream"""
    try:
        # Get basic stats
        total_sessions = db.query(StudySession).filter(
            StudySession.stream_id == stream_id,
            StudySession.is_active == False
        ).count()
        
        active_sessions = db.query(StudySession).filter(
            StudySession.stream_id == stream_id,
            StudySession.is_active == True
        ).count()
        
        total_duration = db.query(func.sum(StudySession.duration_seconds)).filter(
            StudySession.stream_id == stream_id,
            StudySession.is_active == False
        ).scalar() or 0
        
        total_points = db.query(func.sum(StudySession.points_earned)).filter(
            StudySession.stream_id == stream_id,
            StudySession.is_active == False
        ).scalar() or 0
        
        unique_users = db.query(StudySession.user_id).filter(
            StudySession.stream_id == stream_id
        ).distinct().count()
        
        return {
            "stream_id": stream_id,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_duration": total_duration,
            "total_points": total_points,
            "unique_users": unique_users,
            "avg_duration": total_duration / total_sessions if total_sessions > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Get study stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )