from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import (
    AdminBase,
    WithTimestamps,
    WithUUID,
    organization_receive_personal_id_types,
    organization_request_personal_id_types,
)
from app.db.types.oin_type import OinType
from app.models.oin import Oin

if TYPE_CHECKING:
    from app.db.models.certificate import CertificateEntity
    from app.db.models.client import ClientEntity
    from app.db.models.personal_id_type import PersonalIdTypeEntity


class OrganizationEntity(AdminBase, WithUUID, WithTimestamps):
    __tablename__ = "organizations"

    # This is currently pinned to the OIN TYPE. But it's likely that in the future we also
    # need to support additional external_id types.
    external_id: Mapped[Oin] = mapped_column(OinType)
    name: Mapped[str] = mapped_column(String)

    clients: Mapped[list[ClientEntity]] = relationship("ClientEntity", back_populates="organization")

    certificates: Mapped[list[CertificateEntity]] = relationship("CertificateEntity")

    receive_personal_id_types: Mapped[list[PersonalIdTypeEntity]] = relationship(
        secondary=organization_receive_personal_id_types
    )

    request_personal_id_types: Mapped[list[PersonalIdTypeEntity]] = relationship(
        secondary=organization_request_personal_id_types
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            **WithUUID.to_dict(self),
            **WithTimestamps.to_dict(self),
            "external_id": str(self.external_id),
            "name": self.name,
            "receive_personal_id_types": [str(ra.name) for ra in self.receive_personal_id_types],
            "request_personal_id_types": [str(ra.name) for ra in self.request_personal_id_types],
        }
