from datetime import datetime
from uuid import UUID

from cryptography import x509
from pydantic import BaseModel, ConfigDict, field_validator

from app.models.oin import Oin


def _validate_pem_certificate(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        x509.load_pem_x509_certificate(value.encode())
    except Exception:
        raise ValueError("client_certificate must be a valid PEM-encoded X.509 certificate")
    return value


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oin: Oin
    common_name: str
    client_certificate: str | None = None

    @field_validator("client_certificate")
    @classmethod
    def validate_client_certificate(cls, value: str | None) -> str | None:
        return _validate_pem_certificate(value)


class OrganizationUpdate(BaseModel):
    common_name: str
    client_certificate: str | None = None

    @field_validator("client_certificate")
    @classmethod
    def validate_client_certificate(cls, value: str | None) -> str | None:
        return _validate_pem_certificate(value)


class OrganizationQueryParams(BaseModel):
    oin: Oin | None = None


class Organization(OrganizationCreate):
    id: UUID
    created_at: datetime
    deleted_at: datetime | None = None
