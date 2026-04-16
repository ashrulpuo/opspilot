"""Password reset model for OpsPilot."""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class PasswordReset(Base):
    """Password reset token model."""

    __tablename__ = "password_resets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.used and datetime.utcnow() < self.expires_at

    def __repr__(self) -> str:
        return f"<PasswordReset(id={self.id}, user_id={self.user_id}, used={self.used})>"
