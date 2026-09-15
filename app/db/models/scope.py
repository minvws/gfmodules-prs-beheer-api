from __future__ import annotations

from datetime import datetime

from sqlalchemy import INTEGER, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base
from app.enums.authorization_scope import AuthorizationScope
from app.utils.datetime import now_utc


class ScopeEntity(Base):
    __tablename__ = "scopes"
    __table_args__ = ({"schema": "admin"},)

    id: Mapped[int] = mapped_column(
        INTEGER,
        primary_key=True,
    )

    name: Mapped[AuthorizationScope] = mapped_column(Enum(AuthorizationScope), unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
    )
