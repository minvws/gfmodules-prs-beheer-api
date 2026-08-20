from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import UUID, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import AdminBase

if TYPE_CHECKING:
    from app.db.models.organization_request_personal_id_type import OrganizationRequestPersonalIdTypeEntity


class ClientRequestPersonalIdTypeEntity(AdminBase):
    __tablename__ = "client_request_personal_id_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("admin.clients.id"))

    organization_request_personal_id_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("admin.organization_request_personal_id_types.id")
    )
    organization_request_personal_id_type: Mapped[OrganizationRequestPersonalIdTypeEntity] = relationship()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc),
    )
