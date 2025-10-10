"""
Zephy Jr. Bot Control Panel - FastAPI Backend
A full-stack control system for the YouTube Live Chat bot
"""

import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Add the parent directory to Python path to import the original bot
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
import uvicorn

from routers import (
    auth, bot, chat, ai, study, reminders, 
    quiz, points, system
)
from services.bot_runner import BotRunner
from models.database import init_db
from utils.logging_config import setup_logging

# Global bot runner instance
bot_runner = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global bot_runner
    
    # Startup
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting Zephy Jr. Control Panel Backend")
    
    # Initialize database
    await init_db()
    logger.info("✅ Database initialized")
    
    # Initialize bot runner
    bot_runner = BotRunner()
    app.state.bot_runner = bot_runner
    logger.info("✅ Bot runner initialized")
    
    yield
    
    # Shutdown
    if bot_runner:
        await bot_runner.stop_all_bots()
        logger.info("🛑 Bot runner stopped")

# Create FastAPI app
app = FastAPI(
    title="Zephy Jr. Bot Control Panel",
    description="Full-stack control system for YouTube Live Chat bot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://zephyjr.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(bot.router, prefix="/api/bot", tags=["Bot Control"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat Management"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Services"])
app.include_router(study.router, prefix="/api/study", tags=["Study Tracking"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["Reminders"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz System"])
app.include_router(points.router, prefix="/api/points", tags=["Points System"])
app.include_router(system.router, prefix="/api/system", tags=["System Settings"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "zephy-jr-backend",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Zephy Jr. Bot Control Panel API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )