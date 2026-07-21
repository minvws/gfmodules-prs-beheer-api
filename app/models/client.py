from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import INCLUDE_DELETED_DESCRIPTION, Base
from app.models.oin import Oin

COMMON_NAME_DESCRIPTION = "The certificate CN of the client"
OIN_DESCRIPTION = "The OIN of the client"
ORG_OIN_DESCRIPTION = "The OIN identifier of the mandating organization"
SCOPES_DESCRIPTION = "The space separated scopes granted to the client"
ORGANIZATION_NAME_DESCRIPTION = "The name of the organization the client acts on behalf of"


class ClientCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    oin: Oin = Field(..., description=OIN_DESCRIPTION)
    common_name: str = Field(..., description=COMMON_NAME_DESCRIPTION)
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)


class ClientOptionalFields(BaseModel):
    oin: Oin | None = Field(default=None, description=OIN_DESCRIPTION)
    common_name: str | None = Field(default=None, description=COMMON_NAME_DESCRIPTION)
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)


class ClientUpdate(ClientOptionalFields):
    pass


class ClientQueryParams(ClientOptionalFields):
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Client(Base, ClientCreate):
    organization_id: UUID


class ClientResolveRequest(BaseModel):
    oin: Oin = Field(..., description=OIN_DESCRIPTION)
    common_name: str = Field(..., description=COMMON_NAME_DESCRIPTION)
    org_id: Oin = Field(..., description=ORG_OIN_DESCRIPTION)


class ClientResolveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)
    organization_name: str | None = Field(default=None, description=ORGANIZATION_NAME_DESCRIPTION)
