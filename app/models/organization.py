from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.oin import Oin


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oin: Oin
    name: str
    authorizations: str | None = None


class OrganizationUpdate(BaseModel):
    name: str
    authorizations: str | None = None


class OrganizationQueryParams(BaseModel):
    oin: Oin | None = None


class Organization(OrganizationCreate):
    id: UUID
    created_at: datetime
    deleted_at: datetime | None = None
