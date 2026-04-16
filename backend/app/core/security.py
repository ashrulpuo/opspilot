"""Security utilities for authentication and authorization."""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from argon2 import PasswordHasher

from app.core.config import settings


# Password hasher using Argon2 (modern, secure, Python 3.14 compatible)
ph = PasswordHasher(
    time_cost=2,  # Number of iterations
    memory_cost=102400,  # Memory usage in KiB
    parallelism=8,  # Number of parallel threads
    hash_len=32,  # Hash length
    salt_len=16,  # Salt length
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if passwords match, False otherwise
    """
    try:
        return ph.verify(hashed_password, plain_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a plain text password.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return ph.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User information from token

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    if token is None:
        raise credentials_exception

    payload = decode_access_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # TODO: Query user from database and return user object
    # For now, return payload
    return {
        "id": user_id,
        "email": payload.get("email"),
        "full_name": payload.get("full_name"),
    }


def verify_api_key(api_key: str) -> bool:
    """Verify API key for Salt runner authentication.

    Args:
        api_key: API key string

    Returns:
        True if API key is valid, False otherwise
    """
    return api_key == settings.SALT_API_KEY
