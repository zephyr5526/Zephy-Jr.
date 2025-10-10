"""
Quiz system router
"""

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models.database import get_db
from models.schemas import QuizStartRequest, QuizAnswerRequest, QuizResponse
from models.quizzes import Quiz, QuizParticipation
from utils.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/start", response_model=QuizResponse)
async def start_quiz(
    request: QuizStartRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a quiz for a user"""
    try:
        # Check if user already has an active quiz
        active_quiz = db.query(Quiz).filter(
            Quiz.stream_id == request.stream_id,
            Quiz.is_active == True
        ).first()
        
        if active_quiz:
            # Check if user already participated
            participation = db.query(QuizParticipation).filter(
                QuizParticipation.quiz_id == active_quiz.id,
                QuizParticipation.user_id == request.user_id
            ).first()
            
            if participation:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already participated in the current quiz"
                )
            
            # Return existing quiz
            return QuizResponse(
                data={
                    "quiz_id": active_quiz.id,
                    "question": active_quiz.question,
                    "options": active_quiz.options,
                    "points_reward": active_quiz.points_reward,
                    "is_active": True
                }
            )
        
        # Import the original bot's quiz generation function
        from Chatbot_old import generate_quiz_question
        
        # Generate new quiz
        quiz_data = generate_quiz_question()
        
        # Create quiz in database
        quiz = Quiz(
            stream_id=request.stream_id,
            question=quiz_data["question"],
            options=quiz_data["options"],
            correct_answer=quiz_data["answer"],
            explanation=quiz_data.get("explanation", ""),
            points_reward=10.0,
            is_active=True,
            started_at=datetime.utcnow()
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        logger.info(f"🧠 Quiz started for stream {request.stream_id}: {quiz_data['question'][:50]}...")
        
        return QuizResponse(
            data={
                "quiz_id": quiz.id,
                "question": quiz.question,
                "options": quiz.options,
                "points_reward": quiz.points_reward,
                "is_active": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Start quiz error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/answer", response_model=QuizResponse)
async def answer_quiz(
    request: QuizAnswerRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Answer a quiz question"""
    try:
        # Find active quiz
        quiz = db.query(Quiz).filter(
            Quiz.stream_id == request.stream_id,
            Quiz.is_active == True
        ).first()
        
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active quiz found"
            )
        
        # Check if user already answered
        existing_participation = db.query(QuizParticipation).filter(
            QuizParticipation.quiz_id == quiz.id,
            QuizParticipation.user_id == request.user_id
        ).first()
        
        if existing_participation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already answered this quiz"
            )
        
        # Check answer
        is_correct = request.answer.strip().lower() == quiz.correct_answer.strip().lower()
        points_earned = quiz.points_reward if is_correct else 0
        
        # Create participation record
        participation = QuizParticipation(
            quiz_id=quiz.id,
            stream_id=request.stream_id,
            user_id=request.user_id,
            username=request.username,
            answer=request.answer,
            is_correct=is_correct,
            points_earned=points_earned
        )
        db.add(participation)
        db.commit()
        
        logger.info(f"🧠 Quiz answer from {request.username}: {request.answer} ({'correct' if is_correct else 'incorrect'})")
        
        return QuizResponse(
            data={
                "quiz_id": quiz.id,
                "is_correct": is_correct,
                "correct_answer": quiz.correct_answer,
                "explanation": quiz.explanation,
                "points_earned": points_earned,
                "total_participants": db.query(QuizParticipation).filter(
                    QuizParticipation.quiz_id == quiz.id
                ).count()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Answer quiz error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/leaderboard")
async def get_quiz_leaderboard(
    stream_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quiz leaderboard for a stream"""
    try:
        # Get leaderboard data
        leaderboard = db.query(
            QuizParticipation.username,
            func.sum(QuizParticipation.points_earned).label('total_points'),
            func.count(QuizParticipation.id).label('total_answers'),
            func.sum(QuizParticipation.is_correct.cast(db.Integer)).label('correct_answers')
        ).filter(
            QuizParticipation.stream_id == stream_id
        ).group_by(QuizParticipation.username).order_by(
            func.sum(QuizParticipation.points_earned).desc()
        ).limit(limit).all()
        
        data = []
        for i, (username, points, answers, correct) in enumerate(leaderboard, 1):
            accuracy = (correct / answers * 100) if answers > 0 else 0
            data.append({
                "rank": i,
                "username": username,
                "total_points": points,
                "total_answers": answers,
                "correct_answers": correct,
                "accuracy": accuracy
            })
        
        return {
            "stream_id": stream_id,
            "leaderboard": data,
            "total_participants": len(data)
        }
        
    except Exception as e:
        logger.error(f"❌ Get quiz leaderboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/stats")
async def get_quiz_stats(
    stream_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quiz statistics for a stream"""
    try:
        # Get basic stats
        total_quizzes = db.query(Quiz).filter(Quiz.stream_id == stream_id).count()
        active_quizzes = db.query(Quiz).filter(
            Quiz.stream_id == stream_id,
            Quiz.is_active == True
        ).count()
        
        total_participations = db.query(QuizParticipation).filter(
            QuizParticipation.stream_id == stream_id
        ).count()
        
        correct_answers = db.query(QuizParticipation).filter(
            QuizParticipation.stream_id == stream_id,
            QuizParticipation.is_correct == True
        ).count()
        
        total_points = db.query(func.sum(QuizParticipation.points_earned)).filter(
            QuizParticipation.stream_id == stream_id
        ).scalar() or 0
        
        unique_participants = db.query(QuizParticipation.user_id).filter(
            QuizParticipation.stream_id == stream_id
        ).distinct().count()
        
        accuracy = (correct_answers / total_participations * 100) if total_participations > 0 else 0
        
        return {
            "stream_id": stream_id,
            "total_quizzes": total_quizzes,
            "active_quizzes": active_quizzes,
            "total_participations": total_participations,
            "correct_answers": correct_answers,
            "total_points": total_points,
            "unique_participants": unique_participants,
            "accuracy": accuracy
        }
        
    except Exception as e:
        logger.error(f"❌ Get quiz stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )