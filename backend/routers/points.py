"""
Points system router
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models.database import get_db
from models.schemas import PointsResponse, PointsTransactionRequest
from models.points import UserPoints, PointsTransaction
from utils.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/leaderboard", response_model=PointsResponse)
async def get_points_leaderboard(
    stream_id: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get points leaderboard"""
    try:
        # Get leaderboard data
        query = db.query(UserPoints).order_by(desc(UserPoints.total_points))
        
        if stream_id:
            # Filter by stream if provided (this would need additional filtering logic)
            pass
        
        users = query.limit(limit).all()
        
        data = []
        for i, user in enumerate(users, 1):
            data.append({
                "rank": i,
                "user_id": user.user_id,
                "username": user.username,
                "display_name": user.display_name,
                "total_points": user.total_points,
                "study_points": user.study_points,
                "chat_points": user.chat_points,
                "quiz_points": user.quiz_points,
                "bonus_points": user.bonus_points,
                "level": user.level,
                "last_seen": user.updated_at.isoformat() if user.updated_at else None
            })
        
        return PointsResponse(
            data=data,
            total=len(data)
        )
        
    except Exception as e:
        logger.error(f"❌ Get leaderboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/user/{user_id}")
async def get_user_points(
    user_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get points for a specific user"""
    try:
        user_points = db.query(UserPoints).filter(UserPoints.user_id == user_id).first()
        
        if not user_points:
            return {
                "user_id": user_id,
                "total_points": 0,
                "study_points": 0,
                "chat_points": 0,
                "quiz_points": 0,
                "bonus_points": 0,
                "level": 1
            }
        
        return {
            "user_id": user_points.user_id,
            "username": user_points.username,
            "display_name": user_points.display_name,
            "total_points": user_points.total_points,
            "study_points": user_points.study_points,
            "chat_points": user_points.chat_points,
            "quiz_points": user_points.quiz_points,
            "bonus_points": user_points.bonus_points,
            "level": user_points.level,
            "last_seen": user_points.updated_at.isoformat() if user_points.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"❌ Get user points error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/add", response_model=PointsResponse)
async def add_points(
    request: PointsTransactionRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add points to a user"""
    try:
        # Get or create user points record
        user_points = db.query(UserPoints).filter(UserPoints.user_id == request.user_id).first()
        
        if not user_points:
            # Create new user points record
            user_points = UserPoints(
                user_id=request.user_id,
                username="Unknown",  # This should be provided in the request
                total_points=0
            )
            db.add(user_points)
        
        # Add points
        user_points.total_points += request.points
        
        # Update specific category points
        if request.source == "study":
            user_points.study_points += request.points
        elif request.source == "chat":
            user_points.chat_points += request.points
        elif request.source == "quiz":
            user_points.quiz_points += request.points
        elif request.source == "bonus":
            user_points.bonus_points += request.points
        
        # Calculate level (simple formula: level = total_points / 100 + 1)
        user_points.level = int(user_points.total_points / 100) + 1
        
        # Create transaction record
        transaction = PointsTransaction(
            user_id=request.user_id,
            points=request.points,
            transaction_type=request.transaction_type,
            source=request.source,
            description=request.description
        )
        db.add(transaction)
        
        db.commit()
        
        logger.info(f"💰 Added {request.points} points to user {request.user_id} from {request.source}")
        
        return PointsResponse(
            data=[{
                "user_id": user_points.user_id,
                "username": user_points.username,
                "total_points": user_points.total_points,
                "points_added": request.points,
                "new_level": user_points.level
            }]
        )
        
    except Exception as e:
        logger.error(f"❌ Add points error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/transactions/{user_id}")
async def get_user_transactions(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction history for a user"""
    try:
        transactions = db.query(PointsTransaction).filter(
            PointsTransaction.user_id == user_id
        ).order_by(desc(PointsTransaction.timestamp)).limit(limit).all()
        
        data = []
        for transaction in transactions:
            data.append({
                "id": transaction.id,
                "points": transaction.points,
                "transaction_type": transaction.transaction_type,
                "source": transaction.source,
                "description": transaction.description,
                "timestamp": transaction.timestamp.isoformat(),
                "metadata": transaction.metadata
            })
        
        return {
            "user_id": user_id,
            "transactions": data,
            "total": len(data)
        }
        
    except Exception as e:
        logger.error(f"❌ Get user transactions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/stats")
async def get_points_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall points statistics"""
    try:
        # Get basic stats
        total_users = db.query(UserPoints).count()
        total_points = db.query(func.sum(UserPoints.total_points)).scalar() or 0
        total_transactions = db.query(PointsTransaction).count()
        
        # Get top categories
        study_points = db.query(func.sum(UserPoints.study_points)).scalar() or 0
        chat_points = db.query(func.sum(UserPoints.chat_points)).scalar() or 0
        quiz_points = db.query(func.sum(UserPoints.quiz_points)).scalar() or 0
        bonus_points = db.query(func.sum(UserPoints.bonus_points)).scalar() or 0
        
        return {
            "total_users": total_users,
            "total_points": total_points,
            "total_transactions": total_transactions,
            "category_breakdown": {
                "study_points": study_points,
                "chat_points": chat_points,
                "quiz_points": quiz_points,
                "bonus_points": bonus_points
            },
            "average_points_per_user": total_points / total_users if total_users > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Get points stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )