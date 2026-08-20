import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import PrsBase


class HsmKeyVersion(PrsBase):
    __tablename__ = "hsm_key_versions"

    # TODO GB: Create initial hsmKeyVersion when organization is created
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        "organization_id",
        UUID,
        nullable=False,
    )
    version: Mapped[int] = mapped_column("version", Integer, nullable=False)
    from_dt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    until_dt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "version": self.version,
            "from_dt": self.from_dt,
            "until_dt": self.until_dt,
            "removed_at": self.removed_at,
        }
