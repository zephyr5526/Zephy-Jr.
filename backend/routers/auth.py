"""
Authentication router for admin login
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.database import get_db
from models.schemas import LoginRequest, LoginResponse, ErrorResponse
from models.users import AdminUser
from utils.jwt_handler import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Admin login endpoint"""
    try:
        # Find admin user
        admin_user = db.query(AdminUser).filter(
            AdminUser.email == login_data.email,
            AdminUser.is_active == True
        ).first()
        
        if not admin_user:
            logger.warning(f"Login attempt with non-existent email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(login_data.password, admin_user.hashed_password):
            logger.warning(f"Invalid password for email: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Update last login
        admin_user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": admin_user.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"✅ Admin login successful: {login_data.email}")
        
        return LoginResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/logout")
async def logout():
    """Admin logout endpoint (client-side token removal)"""
    return {"message": "Logout successful"}

@router.get("/me")
async def get_current_admin(current_user = Depends(get_current_user)):
    """Get current admin user info"""
    return {
        "email": current_user.email,
        "is_superuser": current_user.is_superuser,
        "last_login": current_user.last_login
    }