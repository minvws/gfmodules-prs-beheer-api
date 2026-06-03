from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Index, String, text
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
    name: Mapped[str] = mapped_column("name", String)
    oin: Mapped[str] = mapped_column("oin", String)
    authorizations: Mapped[Optional[str]] = mapped_column("authorizations", String)
    created_at: Mapped[datetime] = mapped_column("created_at", TIMESTAMP, default=datetime.now)
    deleted_at: Mapped[Optional[datetime]] = mapped_column("deleted_at", TIMESTAMP)
