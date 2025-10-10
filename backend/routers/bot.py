"""
Bot control router
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.database import get_db
from models.schemas import BotStatusResponse, BotStartRequest, BotStopRequest, ErrorResponse
from models.bot_status import BotStatus
from utils.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/start", response_model=BotStatusResponse)
async def start_bot(
    request: BotStartRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start bot for a stream"""
    try:
        # Get bot runner from app state
        from main import app
        bot_runner = app.state.bot_runner
        
        # Start the bot
        success = await bot_runner.start_bot(request.stream_id, request.video_url)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start bot"
            )
        
        # Update database
        bot_status = db.query(BotStatus).filter(BotStatus.stream_id == request.stream_id).first()
        if not bot_status:
            bot_status = BotStatus(stream_id=request.stream_id)
            db.add(bot_status)
        
        bot_status.is_running = True
        bot_status.start_time = datetime.utcnow()
        bot_status.last_activity = datetime.utcnow()
        bot_status.config = {"video_url": request.video_url}
        db.commit()
        
        logger.info(f"✅ Bot started for stream {request.stream_id}")
        
        return BotStatusResponse(
            data={
                "stream_id": request.stream_id,
                "is_running": True,
                "start_time": bot_status.start_time.isoformat(),
                "video_url": request.video_url
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Start bot error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/stop", response_model=BotStatusResponse)
async def stop_bot(
    request: BotStopRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop bot for a stream"""
    try:
        # Get bot runner from app state
        from main import app
        bot_runner = app.state.bot_runner
        
        # Stop the bot
        success = await bot_runner.stop_bot(request.stream_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to stop bot"
            )
        
        # Update database
        bot_status = db.query(BotStatus).filter(BotStatus.stream_id == request.stream_id).first()
        if bot_status:
            bot_status.is_running = False
            bot_status.last_activity = datetime.utcnow()
            db.commit()
        
        logger.info(f"🛑 Bot stopped for stream {request.stream_id}")
        
        return BotStatusResponse(
            data={
                "stream_id": request.stream_id,
                "is_running": False,
                "stop_time": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Stop bot error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(
    stream_id: str = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bot status"""
    try:
        # Get bot runner from app state
        from main import app
        bot_runner = app.state.bot_runner
        
        # Get status from bot runner
        status_data = bot_runner.get_bot_status(stream_id)
        
        # Get additional data from database
        if stream_id:
            bot_status = db.query(BotStatus).filter(BotStatus.stream_id == stream_id).first()
            if bot_status:
                status_data.update({
                    "message_count": bot_status.message_count,
                    "error_count": bot_status.error_count,
                    "config": bot_status.config
                })
        
        return BotStatusResponse(data=status_data)
        
    except Exception as e:
        logger.error(f"❌ Get status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/restart", response_model=BotStatusResponse)
async def restart_bot(
    request: BotStartRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Restart bot for a stream"""
    try:
        # Get bot runner from app state
        from main import app
        bot_runner = app.state.bot_runner
        
        # Restart the bot
        success = await bot_runner.restart_bot(request.stream_id, request.video_url)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to restart bot"
            )
        
        # Update database
        bot_status = db.query(BotStatus).filter(BotStatus.stream_id == request.stream_id).first()
        if not bot_status:
            bot_status = BotStatus(stream_id=request.stream_id)
            db.add(bot_status)
        
        bot_status.is_running = True
        bot_status.start_time = datetime.utcnow()
        bot_status.last_activity = datetime.utcnow()
        bot_status.config = {"video_url": request.video_url}
        db.commit()
        
        logger.info(f"🔄 Bot restarted for stream {request.stream_id}")
        
        return BotStatusResponse(
            data={
                "stream_id": request.stream_id,
                "is_running": True,
                "restart_time": bot_status.start_time.isoformat(),
                "video_url": request.video_url
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Restart bot error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )