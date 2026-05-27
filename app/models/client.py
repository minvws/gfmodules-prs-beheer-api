from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.oin import Oin


class ClientCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oin: Oin
    common_name: str


class ClientUpdate(BaseModel):
    common_name: str


class ClientQueryParams(BaseModel):
    oin: Oin | None = None


class Client(ClientCreate):
    id: UUID
    organization_id: UUID
    created_at: datetime
    deleted_at: datetime | None = None
