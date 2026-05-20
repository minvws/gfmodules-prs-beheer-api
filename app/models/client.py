from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClientCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oin: str
    common_name: str


class ClientUpdate(BaseModel):
    common_name: str


class ClientQueryParams(BaseModel):
    oin: str | None = None


class Client(ClientCreate):
    id: UUID
    organization_id: UUID
    created_at: datetime
    deleted_at: datetime | None = None
