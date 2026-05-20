from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.models.base import Base


class OrganizationEntity(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        Index(
            "uq_organizations_oin_active",
            "oin",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column("id", Uuid, primary_key=True, default=uuid4)
    oin: Mapped[str] = mapped_column("oin", String)
    common_name: Mapped[str] = mapped_column("common_name", String)
    client_certificate: Mapped[Optional[str]] = mapped_column("client_certificate", Text)
    created_at: Mapped[datetime] = mapped_column("created_at", TIMESTAMP, default=datetime.now)
    deleted_at: Mapped[Optional[datetime]] = mapped_column("deleted_at", TIMESTAMP)
