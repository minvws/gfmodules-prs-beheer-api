from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums.authorization_scope import AuthorizationScope
from app.enums.personal_id_type import PersonalIdType
from app.models.base import INCLUDE_DELETED_DESCRIPTION, BaseReadFields
from app.models.oin import Oin

DOMAIN_DESCRIPTION = "The domains from the client certificate's CN and SAN entries"
ORGANIZATION_IDENTIFIER_DESCRIPTION = "The organization_identifier of the client certificate"
EXTERNAL_ID_DESCRIPTION = "The external_id of the Client. Currently limited and transformed to OIN"
CLIENT_ID_DESCRIPTION = "The assigned id of the Cient."
ORGANIZATION_NAME_DESCRIPTION = "The name of the organization the client acts on behalf of"
MATCHED_DOMAIN_DESCRIPTION = "The registered domain that matched one of the presented certificate_domains"


class ClientFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    scopes: list[AuthorizationScope] = Field(examples=[[AuthorizationScope.ADMINISTRATION]])
    request_personal_id_types: list[PersonalIdType] = Field(examples=[[PersonalIdType.OPRF]])
    certificates: list[UUID] = []


class ClientCreate(ClientFields):
    pass


class ClientUpdate(ClientFields):
    deleted: bool = Field(examples=[False])


class ClientQueryParams(BaseModel):
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Client(BaseReadFields, ClientFields):
    organization_id: UUID


class ResolveRequest(BaseModel):
    client_id: UUID = Field(description=CLIENT_ID_DESCRIPTION)
    organization_external_id: Oin = Field(description=EXTERNAL_ID_DESCRIPTION)
    certificate_domains: list[str] = Field(description=DOMAIN_DESCRIPTION)
    certificate_organization_identifier: str = Field(description=ORGANIZATION_IDENTIFIER_DESCRIPTION)


class ResolveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    scopes: str = Field()
    organization_name: str | None = Field(default=None, description=ORGANIZATION_NAME_DESCRIPTION)
    matched_domain: str = Field(description=MATCHED_DOMAIN_DESCRIPTION)
