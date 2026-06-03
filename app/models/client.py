from datetime import datetime
from uuid import UUID

from cryptography import x509
from pydantic import BaseModel, ConfigDict
from pydantic.functional_validators import field_validator

from app.models.oin import Oin


def _validate_pem_certificate(value: str | None) -> str | None:
    if value is None:
        return value

    try:
        x509.load_pem_x509_certificate(value.encode())
    except Exception as exception:
        raise ValueError("certificate must be a valid PEM-encoded X.509 certificate") from exception

    return value


class ClientCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oin: Oin
    common_name: str
    certificate: str | None = None
    allowed_scopes: str | None = None

    @field_validator("certificate")
    @classmethod
    def validate_certificate(cls, value: str | None) -> str | None:
        return _validate_pem_certificate(value)


class ClientUpdate(BaseModel):
    common_name: str
    certificate: str | None = None
    allowed_scopes: str | None = None

    @field_validator("certificate")
    @classmethod
    def validate_certificate(cls, value: str | None) -> str | None:
        return _validate_pem_certificate(value)


class ClientQueryParams(BaseModel):
    oin: Oin | None = None


class Client(ClientCreate):
    id: UUID
    organization_id: UUID
    created_at: datetime
    deleted_at: datetime | None = None
