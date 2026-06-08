from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.client import ClientEntity
    from app.db.models.organization_scope import OrganizationScopeEntity


class OrganizationEntity(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        Index(
            "uq_organizations_register_id_active",
            "register_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column("id", Uuid, primary_key=True, default=uuid4)
    register_id: Mapped[str] = mapped_column(
        "register_id", String
    )  # ID of the organization: {OIN} for PRS - {URA} for NVI
    name: Mapped[str] = mapped_column("name", String)
    created_at: Mapped[datetime] = mapped_column("created_at", TIMESTAMP, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column("deleted_at", TIMESTAMP)

    clients: Mapped[List["ClientEntity"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan", lazy="raise"
    )
    organization_scopes: Mapped[List["OrganizationScopeEntity"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan", lazy="raise"
    )
