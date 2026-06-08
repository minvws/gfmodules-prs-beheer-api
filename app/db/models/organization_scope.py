from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import OrganizationEntity
    from app.db.models.scope import ScopeEntity


class OrganizationScopeEntity(Base):
    __tablename__ = "organization_scopes"

    organization_id: Mapped[UUID] = mapped_column(
        "organization_id", Uuid, ForeignKey("organizations.id"), primary_key=True
    )
    scope_id: Mapped[UUID] = mapped_column("scope_id", Uuid, ForeignKey("scopes.id"), primary_key=True)

    organization: Mapped["OrganizationEntity"] = relationship(back_populates="organization_scopes", lazy="raise")
    scope: Mapped["ScopeEntity"] = relationship(back_populates="organization_scopes", lazy="raise")
