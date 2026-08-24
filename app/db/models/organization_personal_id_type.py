from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import UUID, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import ClientEntity
from app.db.models.base import AdminBase
from app.db.models.personal_id_type import PersonalIdTypeEntity


class OrganizationPersonalIdTypeEntity(AdminBase):
    __tablename__ = "client_request_personal_id_types"

    client_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("admin.clients.id"), primary_key=True)

    personal_id_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("admin.personal_id_types.id"), primary_key=True
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("admin.organizations.id"), primary_key=True)

    client: Mapped[ClientEntity] = relationship()

    personal_id_type: Mapped[PersonalIdTypeEntity] = relationship()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc),
    )
