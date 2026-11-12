"""Login session model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class UserSession(Base):
    """One issued login token, stored only as the sha256 hex digest of the token."""
    __tablename__ = "user_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime]
    expires_at: Mapped[datetime] = mapped_column(index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
