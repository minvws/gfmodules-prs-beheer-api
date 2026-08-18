from __future__ import annotations
from datetime import datetime, timezone
import uuid

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, String, text, UUID, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.models.base import Base
from app.db.types.oin_type import OinType
from app.models.oin import Oin

if TYPE_CHECKING:
    from app.db.models.client_request_personal_id_type import ClientRequestPersonalIdTypeEntity
    from app.db.models.organization import OrganizationEntity


class ClientEntity(Base):
    __tablename__ = "clients"
    __table_args__ = {"schema": "admin"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # This is currently pinned to the OIN TYPE. But it's likely that in the future we also
    # need to support additional external_id types.
    external_id: Mapped[Oin] = mapped_column(OinType())

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID)

    common_name: Mapped[str] = mapped_column(String)

    request_personal_id_types: Mapped[list["ClientRequestPersonalIdTypeEntity"]] = relationship(
        "ClientRequestPersonalIdTypeEntity", cascade="all, delete-orphan"
    )

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
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "external_id": str(self.external_id),
            "common_name": self.common_name,
            "organization_id": self.organization_id,
            "request_personal_id_types": [
                ra.organization_request_personal_id_type.personal_id_type for ra in self.request_personal_id_types
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }
