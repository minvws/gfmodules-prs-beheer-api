from app.db.models.base import Base
from uuid import UUID
from datetime import datetime
import string
from pydantic import BaseModel, ConfigDict


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
    pass


class Certificate(CertificateFields, CertificateReadFields):
    pass
