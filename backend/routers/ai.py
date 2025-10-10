"""
AI services router
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import AIRequest, AIResponse, ErrorResponse
from utils.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/reply", response_model=AIResponse)
async def generate_ai_reply(
    request: AIRequest,
    current_user = Depends(get_current_user)
):
    """Generate AI reply using OpenRouter or Gemini"""
    try:
        # Import the original bot's AI function
        from Chatbot_old import call_openai_api
        
        # Generate response
        response = call_openai_api(
            system_prompt="You are Zephy Jr., a witty and sarcastic YouTube chatbot. Reply in a short, funny way.",
            user_prompt=request.prompt
        )
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate AI response"
            )
        
        logger.info(f"🤖 AI reply generated: {response[:50]}...")
        
        return AIResponse(
            data={
                "reply": response,
                "model": "openrouter",
                "prompt": request.prompt,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ AI reply error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/models")
async def get_available_models(current_user = Depends(get_current_user)):
    """Get available AI models"""
    try:
        # Import from original bot
        from Chatbot_old import PREFERRED_MODELS, CURRENT_MODEL
        
        return {
            "current_model": CURRENT_MODEL,
            "available_models": PREFERRED_MODELS,
            "model_info": {
                "openai/gpt-4.1": "Best GPT-4 model",
                "openai/gpt-4o": "Optimized GPT-4",
                "openai/gpt-3.5-turbo": "Cheaper OpenAI model",
                "mistralai/mixtral-8x7b-instruct": "Lightweight model",
                "mistralai/mistral-7b-instruct": "Larger & smarter model"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Get models error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/test")
async def test_ai_connection(current_user = Depends(get_current_user)):
    """Test AI service connection"""
    try:
        # Import the original bot's AI function
        from Chatbot_old import call_openai_api
        
        # Test with a simple prompt
        response = call_openai_api(
            system_prompt="You are a test bot. Reply with 'Test successful'.",
            user_prompt="Test message"
        )
        
        if response:
            return {
                "status": "success",
                "message": "AI service is working",
                "test_response": response
            }
        else:
            return {
                "status": "error",
                "message": "AI service is not responding"
            }
        
    except Exception as e:
        logger.error(f"❌ AI test error: {e}")
        return {
            "status": "error",
            "message": f"AI service error: {str(e)}"
        }