from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import INCLUDE_DELETED_DESCRIPTION


class CertificateReadFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class CertificateFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_identifier: str
    domain: str


class CertificateQueryParams(BaseModel):
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Certificate(CertificateFields, CertificateReadFields):
    pass
