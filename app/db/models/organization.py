from __future__ import annotations
import uuid
from datetime import timezone, datetime

from typing import TYPE_CHECKING, Any

from sqlalchemy import Index, String, text, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base
from app.db.types.oin_type import OinType
from app.models.oin import Oin

if TYPE_CHECKING:
    from app.db.models.client import ClientEntity
    from app.db.models.organization_receive_personal_id_type import OrganizationReceivePersonalIdTypeEntity
    from app.db.models.organization_request_personal_id_type import OrganizationRequestPersonalIdTypeEntity


class OrganizationEntity(Base):
    __tablename__ = "organizations"
    __table_args__ = {"schema": "admin"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # This is currently pinned to the OIN TYPE. But it's likely that in the future we also
    # need to support additional external_id types.
    external_id: Mapped[Oin] = mapped_column(OinType)
    name: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    receive_personal_id_types: Mapped[list["OrganizationReceivePersonalIdTypeEntity"]] = relationship(
        "OrganizationReceivePersonalIdTypeEntity", cascade="all, delete-orphan"
    )

    request_personal_id_types: Mapped[list["OrganizationRequestPersonalIdTypeEntity"]] = relationship(
        "OrganizationRequestPersonalIdTypeEntity", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "external_id": str(self.external_id),
            "name": self.name,
            "receive_personal_id_types": [ra.personal_id_type for ra in self.receive_personal_id_types],
            "request_personal_id_types": [ra.personal_id_type for ra in self.request_personal_id_types],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }
