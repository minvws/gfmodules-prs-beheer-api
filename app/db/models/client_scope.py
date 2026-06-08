from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.client import ClientEntity
    from app.db.models.scope import ScopeEntity


class ClientScopeEntity(Base):
    __tablename__ = "client_scopes"

    client_id: Mapped[UUID] = mapped_column("client_id", Uuid, ForeignKey("clients.id"), primary_key=True)
    scope_id: Mapped[UUID] = mapped_column("scope_id", Uuid, ForeignKey("scopes.id"), primary_key=True)

    client: Mapped["ClientEntity"] = relationship(back_populates="client_scopes", lazy="raise")
    scope: Mapped["ScopeEntity"] = relationship(back_populates="client_scopes", lazy="raise")
