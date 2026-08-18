from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import UUID, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import AdminBase
from app.enums.personal_id_type import PersonalIdType


class OrganizationReceivePersonalIdTypeEntity(AdminBase):
    __tablename__ = "organization_receive_personal_id_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("admin.organizations.id"))
    personal_id_type: Mapped[PersonalIdType] = mapped_column(Enum(PersonalIdType))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc),
    )
