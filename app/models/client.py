from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums.personal_id_type import PersonalIdType
from app.models.base import INCLUDE_DELETED_DESCRIPTION, Base
from app.models.oin import Oin

DOMAIN_DESCRIPTION = "The domain of the client certificate registered in the CN or the SAN"
ORGANIZATION_IDENTIFIER_DESCRIPTION = "The organization_identifier of the client certificate"
EXTERNAL_ID_DESCRIPTION = "The external_id of the Client. Currently limited and transformed to OIN"
CLIENT_ID_DESCRIPTION = "The assigned id of the Cient."
ORGANIZATION_NAME_DESCRIPTION = "The name of the organization the client acts on behalf of"


class ClientReadFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ClientFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    request_personal_id_types: list[PersonalIdType] = Field(examples=[[PersonalIdType.OPRF]])
    certificates: list[UUID] = []


class ClientCreate(ClientFields):
    pass


class ClientUpdate(ClientFields):
    deleted: bool = Field(examples=[False])


class ClientQueryParams(BaseModel):
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Client(Base, ClientReadFields, ClientFields):
    organization_id: UUID


class DeprecatedResolveRequest(BaseModel):
    # TODO DEprecated message
    client_organization_id: Oin = Field(description=ORGANIZATION_IDENTIFIER_DESCRIPTION, deprecated=True)
    client_common_name: str = Field(description=DOMAIN_DESCRIPTION, deprecated=True)
    organization_id: Oin = Field(description=EXTERNAL_ID_DESCRIPTION, deprecated=True)


# TODO GB Make backwards compatible
class ResolveRequest(BaseModel):
    client_id: UUID | None = Field(description=CLIENT_ID_DESCRIPTION, default=None)
    organization_external_id: Oin = Field(description=EXTERNAL_ID_DESCRIPTION)
    certificate_domain: str = Field(description=DOMAIN_DESCRIPTION)
    certificate_organization_identifier: str = Field(description=ORGANIZATION_IDENTIFIER_DESCRIPTION)


class ResolveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    scopes: str = Field()
    organization_name: str | None = Field(default=None, description=ORGANIZATION_NAME_DESCRIPTION)
