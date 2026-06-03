from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.models.base import Base


class ClientEntity(Base):
    __tablename__ = "clients"
    __table_args__ = (
        Index(
            "uq_clients_org_oin_active",
            "organization_id",
            "oin",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column("id", Uuid, primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column("organization_id", Uuid, ForeignKey("organizations.id"))
    oin: Mapped[str] = mapped_column("oin", String)
    certificate: Mapped[Optional[str]] = mapped_column("certificate", Text)
    allowed_scopes: Mapped[Optional[str]] = mapped_column("allowed_scopes", String)
    common_name: Mapped[str] = mapped_column("common_name", String)
    created_at: Mapped[datetime] = mapped_column("created_at", TIMESTAMP, default=datetime.now)
    deleted_at: Mapped[Optional[datetime]] = mapped_column("deleted_at", TIMESTAMP)
