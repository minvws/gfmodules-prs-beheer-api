from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.oin import Oin

MANDATE_ID_DESCRIPTION = "The ID the client is mandated for: 'ORG_ID' or 'ORG_ID:DEVICE_ID'"
COMMON_NAME_DESCRIPTION = "The certificate CN of the client"
OIN_DESCRIPTION = "The OIN of the client"
SCOPES_DESCRIPTION = "The space separated scopes granted to the client"
INCLUDE_DELETED_DESCRIPTION = "Include soft-deleted clients in the results"


class ClientCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oin: Oin = Field(..., description=OIN_DESCRIPTION)
    common_name: str = Field(..., description=COMMON_NAME_DESCRIPTION)
    mandate_id: str = Field(..., description=MANDATE_ID_DESCRIPTION)
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)


class ClientOptionalFields(BaseModel):
    oin: Oin | None = Field(default=None, description=OIN_DESCRIPTION)
    common_name: str | None = Field(default=None, description=COMMON_NAME_DESCRIPTION)
    mandate_id: str | None = Field(default=None, description=MANDATE_ID_DESCRIPTION)
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)


class ClientUpdate(ClientOptionalFields):
    pass


class ClientQueryParams(ClientOptionalFields):
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Client(ClientCreate):
    id: UUID
    organization_id: UUID
    created_at: datetime
    deleted_at: datetime | None = None


class ClientResolveRequest(BaseModel):
    oin: Oin = Field(..., description=OIN_DESCRIPTION)
    common_name: str = Field(..., description=COMMON_NAME_DESCRIPTION)
    mandate_id: str = Field(..., description=MANDATE_ID_DESCRIPTION)
