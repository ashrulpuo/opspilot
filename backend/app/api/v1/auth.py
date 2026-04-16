"""Authentication endpoints."""
import secrets
import uuid
from datetime import timedelta, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import redis.asyncio as redis

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    get_current_user as get_current_user_dep,
)
from app.models.user import User
from app.models.organization import Organization, OrganizationMember
from app.models.password_reset import PasswordReset
from app.core.database import get_db
from app.core.email import email_service
from app.core.config import settings

router = APIRouter()


# Redis client for rate limiting
async def get_redis_client():
    """Get Redis client for rate limiting."""
    return redis.from_url(settings.REDIS_URL)


async def check_rate_limit(
    redis_client: redis.Redis,
    key: str,
    max_attempts: int = 5,
    window_seconds: int = 3600
) -> bool:
    """Check rate limit for a given key.

    Args:
        redis_client: Redis client
        key: Rate limit key
        max_attempts: Maximum allowed attempts
        window_seconds: Time window in seconds

    Returns:
        True if rate limit check passes, False otherwise
    """
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)
        return current <= max_attempts
    except Exception:
        # If Redis fails, allow the request (fail-open)
        return True


async def get_rate_limit_ttl(
    redis_client: redis.Redis,
    key: str
) -> int:
    """Get remaining TTL for rate limit key.

    Args:
        redis_client: Redis client
        key: Rate limit key

    Returns:
        Remaining TTL in seconds, or 0 if not rate limited
    """
    try:
        ttl = await redis_client.ttl(key)
        return max(0, ttl)
    except Exception:
        return 0


# Request Schemas
class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr
    password: str
    full_name: str
    confirm_password: str

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Validate that password and confirm_password match."""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class TokenRefreshRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str


# Response Schemas
class LoginResponse(BaseModel):
    """Login response schema."""

    access_token: str
    token_type: str = "bearer"
    user: dict


class RegisterResponse(BaseModel):
    """Registration response schema."""

    message: str
    user_id: str


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    email: str
    full_name: str
    is_active: bool


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema."""

    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Forgot password response schema."""

    message: str


class ResetPasswordRequest(BaseModel):
    """Reset password request schema."""

    token: str
    new_password: str
    confirm_password: str

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """Validate that password and confirm_password match."""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class ResetPasswordResponse(BaseModel):
    """Reset password response schema."""

    message: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """User login.

    Args:
        request: Login request with email and password
        db: Database session

    Returns:
        Login response with access token and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create access token
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "full_name": user.full_name,
        },
        expires_delta=access_token_expires,
    )

    return LoginResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        }
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """User registration.

    Args:
        request: Registration request with user details
        db: Database session

    Returns:
        Registration response with user ID

    Raises:
        HTTPException: If email already exists
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    import uuid
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=request.email,
        password_hash=get_password_hash(request.password),
        full_name=request.full_name,
        is_active=True,
    )

    # Create personal organization for new user
    org_id = str(uuid.uuid4())
    org = Organization(
        id=org_id,
        name=f"{request.full_name}'s Organization",
        slug=request.email.split("@")[0],
    )

    # Add user as admin of organization
    org_member = OrganizationMember(
        user_id=user_id,
        organization_id=org_id,
        role="admin",
    )

    db.add(user)
    db.add(org)
    db.add(org_member)
    await db.commit()

    return RegisterResponse(
        message="User registered successfully",
        user_id=user_id,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: dict = Depends(get_current_user_dep),
):
    """Get current authenticated user.

    Args:
        current_user: Current user from JWT token

    Returns:
        Current user information
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        is_active=True,
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: TokenRefreshRequest):
    """Refresh access token.

    Args:
        request: Token refresh request

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Decode refresh token
    payload = decode_access_token(request.refresh_token)
    user_id: str = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Create new access token
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={
            "sub": user_id,
            "email": payload.get("email"),
            "full_name": payload.get("full_name"),
        },
        expires_delta=access_token_expires,
    )

    return LoginResponse(
        access_token=access_token,
        user={
            "id": user_id,
            "email": payload.get("email"),
            "full_name": payload.get("full_name"),
        }
    )


@router.post("/logout")
async def logout():
    """User logout.

    Note: JWT tokens are stateless, so this is mainly for
    client-side cleanup. Token invalidation can be
    implemented with a blacklist if needed.
    """
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Initiate password reset process.

    This endpoint generates a secure reset token and sends it via email.
    Rate limited to 5 requests per hour per email.

    Args:
        request: Forgot password request with email
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If rate limit is exceeded or email not found
    """
    redis_client = await get_redis_client()
    rate_limit_key = f"password_reset_rate:{request.email}"

    # Check rate limit (5 requests per hour)
    if not await check_rate_limit(redis_client, rate_limit_key, max_attempts=5, window_seconds=3600):
        ttl = await get_rate_limit_ttl(redis_client, rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many password reset requests. Please try again in {ttl} seconds.",
        )

    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    # Only send email if user exists
    if user:
        # Generate secure random token
        token_id = str(uuid.uuid4())
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        # Save token to database
        password_reset = PasswordReset(
            id=token_id,
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at,
            used=False
        )
        db.add(password_reset)

        # Invalidate previous tokens for this user
        await db.execute(
            select(PasswordReset).where(
                and_(
                    PasswordReset.user_id == user.id,
                    PasswordReset.id != token_id
                )
            )
        )
        # Mark old tokens as used
        old_tokens_result = await db.execute(
            select(PasswordReset).where(
                and_(
                    PasswordReset.user_id == user.id,
                    PasswordReset.id != token_id,
                    PasswordReset.used == False
                )
            )
        )
        old_tokens = old_tokens_result.scalars().all()
        for old_token in old_tokens:
            old_token.used = True

        await db.commit()

        # Send password reset email
        reset_url = f"{settings.app_url}/reset-password?token={reset_token}"
        email_service.send_password_reset_email(
            to_email=user.email,
            user_name=user.full_name,
            reset_url=reset_url
        )

    await redis_client.close()

    return ForgotPasswordResponse(
        message="If an account exists with this email, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reset password using token.

    This endpoint validates the reset token and updates the user's password.
    Tokens are single-use and expire after 15 minutes.

    Args:
        request: Reset password request with token and new password
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If token is invalid, expired, or already used
    """
    # Find token in database
    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.token == request.token
        )
    )
    password_reset = result.scalar_one_or_none()

    # Validate token
    if not password_reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Check if token is already used
    if password_reset.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used",
        )

    # Check if token is expired
    if datetime.utcnow() > password_reset.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    # Get user
    user_result = await db.execute(
        select(User).where(User.id == password_reset.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update user's password
    user.password_hash = get_password_hash(request.new_password)
    user.updated_at = datetime.utcnow()

    # Mark token as used
    password_reset.used = True

    # Invalidate all other reset tokens for this user
    other_tokens_result = await db.execute(
        select(PasswordReset).where(
            and_(
                PasswordReset.user_id == user.id,
                PasswordReset.id != password_reset.id,
                PasswordReset.used == False
            )
        )
    )
    other_tokens = other_tokens_result.scalars().all()
    for other_token in other_tokens:
        other_token.used = True

    await db.commit()

    return ResetPasswordResponse(
        message="Password has been reset successfully. You can now login with your new password."
    )
