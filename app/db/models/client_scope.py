from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID, DateTime, ForeignKey, ForeignKeyConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import ClientEntity
from app.db.models.base import Base
from app.db.models.scope import ScopeEntity
from app.utils.datetime import now_utc


class ClientScopeEntity(Base):
    __tablename__ = "client_scopes"
    __table_args__: tuple[Any, ...] = (
        ForeignKeyConstraint(
            ["organization_id", "scope_id"],
            [
                "admin.organization_scopes.organization_id",
                "admin.organization_scopes.scope_id",
            ],
        ),
        {"schema": "admin"},
    )

    client_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("admin.clients.id"), primary_key=True)

    scope_id: Mapped[int] = mapped_column(Integer, ForeignKey("admin.scopes.id"), primary_key=True)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("admin.organizations.id"), primary_key=True)

    client: Mapped[ClientEntity] = relationship(back_populates="scopes")

    scope: Mapped[ScopeEntity] = relationship()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
    )
