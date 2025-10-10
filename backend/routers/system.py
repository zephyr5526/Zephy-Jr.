"""
System settings router
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from models.database import get_db
from models.schemas import SystemSettingRequest, SystemSettingResponse
from models.system_settings import SystemSetting, APIConfig
from utils.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/settings")
async def get_system_settings(
    category: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system settings"""
    try:
        query = db.query(SystemSetting)
        
        if category:
            query = query.filter(SystemSetting.category == category)
        
        settings = query.all()
        
        data = {}
        for setting in settings:
            # Convert value based on type
            if setting.value_type == "int":
                value = int(setting.value)
            elif setting.value_type == "float":
                value = float(setting.value)
            elif setting.value_type == "bool":
                value = setting.value.lower() in ("true", "1", "yes", "on")
            elif setting.value_type == "json":
                import json
                value = json.loads(setting.value)
            else:
                value = setting.value
            
            data[setting.key] = {
                "value": value,
                "type": setting.value_type,
                "description": setting.description,
                "category": setting.category,
                "is_public": setting.is_public
            }
        
        return {
            "settings": data,
            "total": len(settings)
        }
        
    except Exception as e:
        logger.error(f"❌ Get settings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/settings", response_model=SystemSettingResponse)
async def update_system_setting(
    request: SystemSettingRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a system setting"""
    try:
        # Convert value to string based on type
        if isinstance(request.value, bool):
            value_str = str(request.value).lower()
            value_type = "bool"
        elif isinstance(request.value, int):
            value_str = str(request.value)
            value_type = "int"
        elif isinstance(request.value, float):
            value_str = str(request.value)
            value_type = "float"
        elif isinstance(request.value, dict):
            import json
            value_str = json.dumps(request.value)
            value_type = "json"
        else:
            value_str = str(request.value)
            value_type = "string"
        
        # Get or create setting
        setting = db.query(SystemSetting).filter(SystemSetting.key == request.key).first()
        
        if setting:
            setting.value = value_str
            setting.value_type = value_type
            if request.description:
                setting.description = request.description
        else:
            setting = SystemSetting(
                key=request.key,
                value=value_str,
                value_type=value_type,
                description=request.description or "",
                category="system"
            )
            db.add(setting)
        
        db.commit()
        
        logger.info(f"⚙️ Updated setting {request.key} = {request.value}")
        
        return SystemSettingResponse(
            data={
                "key": setting.key,
                "value": request.value,
                "type": value_type,
                "description": setting.description,
                "category": setting.category
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Update setting error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/api-config")
async def get_api_config(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API configuration (without sensitive keys)"""
    try:
        configs = db.query(APIConfig).all()
        
        data = []
        for config in configs:
            data.append({
                "id": config.id,
                "service_name": config.service_name,
                "is_active": config.is_active,
                "last_used": config.last_used.isoformat() if config.last_used else None,
                "usage_count": config.usage_count,
                "error_count": config.error_count,
                "has_key": bool(config.api_key)
            })
        
        return {
            "api_configs": data,
            "total": len(data)
        }
        
    except Exception as e:
        logger.error(f"❌ Get API config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/api-config")
async def update_api_config(
    service_name: str,
    api_key: str,
    is_active: bool = True,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update API configuration"""
    try:
        # Get or create API config
        config = db.query(APIConfig).filter(APIConfig.service_name == service_name).first()
        
        if config:
            config.api_key = api_key
            config.is_active = is_active
        else:
            config = APIConfig(
                service_name=service_name,
                api_key=api_key,
                is_active=is_active
            )
            db.add(config)
        
        db.commit()
        
        logger.info(f"🔑 Updated API config for {service_name}")
        
        return {
            "message": f"API configuration updated for {service_name}",
            "service_name": service_name,
            "is_active": is_active
        }
        
    except Exception as e:
        logger.error(f"❌ Update API config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/health")
async def get_system_health(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system health status"""
    try:
        # Get bot runner status
        from main import app
        bot_runner = app.state.bot_runner
        bot_status = bot_runner.get_bot_status()
        
        # Get database status
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"
        
        # Get basic stats
        from models.chat_logs import ChatLog
        from models.study_sessions import StudySession
        from models.points import UserPoints
        
        total_messages = db.query(ChatLog).count()
        total_sessions = db.query(StudySession).count()
        total_users = db.query(UserPoints).count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": db_status,
                "bot_runner": "healthy" if bot_runner else "unhealthy"
            },
            "stats": {
                "total_messages": total_messages,
                "total_sessions": total_sessions,
                "total_users": total_users,
                "active_bots": bot_status.get("total_running", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Get system health error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }