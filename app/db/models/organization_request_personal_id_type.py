from __future__ import annotations
from pydantic.v1.schema import schema
import uuid
from datetime import timezone, datetime

from typing import TYPE_CHECKING, Any

from sqlalchemy import Index, String, text, DateTime, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base
from app.db.types.oin_type import OinType
from app.models.oin import Oin

if TYPE_CHECKING:
    from app.db.models.client import ClientEntity
    from app.db.models.organization import OrganizationEntity


class OrganizationRequestPersonalIdTypeEntity(Base):
    __tablename__ = "organization_request_personal_id_types"
    __table_args__ = {"schema": "admin"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("admin.organizations.id"))
    personal_id_type: Mapped[str] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc),
    )
