from __future__ import annotations

from typing import TYPE_CHECKING, List
from uuid import UUID, uuid4

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.client_scope import ClientScopeEntity
    from app.db.models.organization_scope import OrganizationScopeEntity


class ScopeEntity(Base):
    __tablename__ = "scopes"

    id: Mapped[UUID] = mapped_column("id", Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column("name", String, unique=True)
    active: Mapped[bool] = mapped_column("active", Boolean, default=True)

    organization_scopes: Mapped[List["OrganizationScopeEntity"]] = relationship(
        back_populates="scope", cascade="all", lazy="raise"
    )
    client_scopes: Mapped[List["ClientScopeEntity"]] = relationship(back_populates="scope", cascade="all", lazy="raise")
