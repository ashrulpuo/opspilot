"""Password reset endpoints for OpsPilot."""
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.email import email_service
from app.core.security import verify_password
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.core.security import get_password_hash

router = APIRouter()

# Rate limiting (in-memory for simplicity - use Redis in production)
reset_attempts = {}


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password."""
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    """Request model for reset password."""
    token: str = Field(..., min_length=32, max_length=255, description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")


@router.post("/auth/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request password reset email."""
    
    # Check rate limiting (max 3 requests per 15 minutes per email)
    now = datetime.utcnow()
    if request.email in reset_attempts:
        attempts, last_attempt = reset_attempts[request.email]
        if len(attempts) >= 3 and (now - last_attempt) < timedelta(minutes=15):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset requests. Please try again later.",
            )
        # Clean old attempts (older than 15 minutes)
        reset_attempts[request.email] = attempts[-3:] if len(attempts) >= 3 else attempts
    else:
        reset_attempts[request.email] = []
    
    reset_attempts[request.email].append(now)
    
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists (security)
        return {"message": "If an account with this email exists, you will receive a reset link shortly."}
    
    # Generate secure random token
    token = secrets.token_urlsafe(64)
    
    # Create password reset record
    password_reset = PasswordReset(
        id=token,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        used=False
    )
    db.add(password_reset)
    await db.commit()
    
    # Send email with reset link
    reset_link = f"https://app.opspilot.com/reset-password?token={token}"
    
    success = email_service.send_password_reset_email(
        to_emails=[user.email],
        user_name=user.full_name,
        reset_link=reset_link,
        expires_at=password_reset.expires_at.isoformat()
    )
    
    return {"message": "If an account with this email exists, you will receive a reset link shortly."}


@router.post("/auth/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password with token."""
    
    # Find password reset token
    result = await db.execute(
        select(PasswordReset).where(PasswordReset.id == request.token)
    )
    password_reset = result.scalar_one_or_none()
    
    # Validate token
    if not password_reset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired reset token.",
        )
    
    if password_reset.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used.",
        )
    
    if datetime.utcnow() > password_reset.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new password reset.",
        )
    
    # Find user
    result = await db.execute(
        select(User).where(User.id == password_reset.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    
    # Mark token as used
    password_reset.used = True
    await db.commit()
    
    # Clean rate limiting entry
    if user.email in reset_attempts:
        del reset_attempts[user.email]
    
    return {"message": "Password reset successfully. Please login with your new password."}
