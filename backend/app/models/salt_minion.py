"""Salt minion model."""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql

from app.core.database import Base


class SaltMinion(Base):
    """Salt minion model."""
    
    __tablename__ = "salt_minions"
    
    id = Column(String, primary_key=True)
    minion_id = Column(String, nullable=False, index=True)
    server_id = Column(String, ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True)
    last_seen = Column(DateTime, nullable=False, index=True)
    last_highstate = Column(DateTime, nullable=True)
    os_info = Column(postgresql.JSONB(), nullable=False)
    grains_info = Column(postgresql.JSONB(), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
