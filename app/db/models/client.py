from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.organization import OrganizationEntity


class ClientEntity(Base):
    __tablename__ = "clients"
    __table_args__ = (
        Index(
            "uq_clients_org_mandate_active",
            "organization_id",
            "mandate_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column("id", Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column("organization_id", Uuid, ForeignKey("organizations.id"))
    mandate_id: Mapped[str] = mapped_column(
        "mandate_id",
        String,  # ID of organization that has given mandate for to act on its behalf: {OIN} for PRS - {URA:DEVICE_ID} for NVI.
    )  # Should correspond with the register_id of the organization referenced by organization_id

    oin: Mapped[str] = mapped_column("oin", String)  # OIN of the client
    common_name: Mapped[str] = mapped_column("common_name", String)
    scopes: Mapped[Optional[str]] = mapped_column("scopes", String)
    created_at: Mapped[datetime] = mapped_column("created_at", TIMESTAMP, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column("deleted_at", TIMESTAMP)

    organization: Mapped["OrganizationEntity"] = relationship(back_populates="clients", lazy="raise")
