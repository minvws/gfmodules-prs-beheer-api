from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.base import PersonalIdType
from app.models.base import INCLUDE_DELETED_DESCRIPTION, Base
from app.models.oin import Oin

COMMON_NAME_DESCRIPTION = "The certificate CN of the client"
EXTERNAL_ID_DESCRIPTION = "The external_id of the Client. Currently limitted and transformed to OIN"
ORG_OIN_DESCRIPTION = "The OIN identifier of the mandating organization"
SCOPES_DESCRIPTION = "The space separated scopes granted to the client"
ORGANIZATION_NAME_DESCRIPTION = "The name of the organization the client acts on behalf of"


class ClientReadFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ClientFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    external_id: Oin = Field(description=EXTERNAL_ID_DESCRIPTION)
    common_name: str = Field(description="The common_name or SAN on which the client is authorized")
    request_personal_id_types: list[PersonalIdType] = Field(example=[PersonalIdType.OPRF])


class ClientCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: Oin = Field(..., description=EXTERNAL_ID_DESCRIPTION)
    common_name: str = Field(..., description=COMMON_NAME_DESCRIPTION)
    request_personal_id_types: list[PersonalIdType] = Field(example=[PersonalIdType.OPRF])


class ClientUpdate(ClientFields):
    pass


class ClientQueryParams(BaseModel):
    external_id: Oin | None = Field(default=None, description=EXTERNAL_ID_DESCRIPTION)
    common_name: str | None = Field(default=None, description=COMMON_NAME_DESCRIPTION)
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Client(Base, ClientReadFields, ClientCreate):
    organization_id: UUID


class ClientResolveRequest(BaseModel):
    client_organization_id: Oin = Field(..., description=EXTERNAL_ID_DESCRIPTION)
    client_common_name: str = Field(..., description=COMMON_NAME_DESCRIPTION)
    organization_id: UUID = Field(..., description=ORG_OIN_DESCRIPTION)


class ClientResolveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    organization_name: str | None = Field(default=None, description=ORGANIZATION_NAME_DESCRIPTION)
