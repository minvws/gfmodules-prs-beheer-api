from typing import Any
from app.models.oin import Oin
from app.db.models.base import AdminBase, WithTimestamps
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import UUID, String, ForeignKey
import uuid


class CertificateEntity(AdminBase, WithTimestamps):
    __tablename__ = "certificates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_identifier: Mapped[str] = mapped_column(String)

    domain: Mapped[str] = mapped_column(String)

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("admin.organizations.id"))

    def to_dict(self) -> dict[str, Any]:
        return {
            **WithTimestamps.to_dict(self),
            "id": self.id,
            "organization_identifier": self.organization_identifier,
            "domain": self.domain,
            "organization_id": self.organization_id,
        }
