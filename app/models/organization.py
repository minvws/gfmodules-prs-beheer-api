from pydantic import BaseModel, ConfigDict, Field

from app.enums.personal_id_type import PersonalIdType
from app.models.base import INCLUDE_DELETED_DESCRIPTION, BaseReadFields
from app.models.oin import Oin

EXTERNAL_ID_DESCRIPTION = "The OIN of the organization"
NAME_DESCRIPTION = "The name of the organization"
SCOPES_DESCRIPTION = "The space separated scopes granted to the organization"


class OrganizationRequestAuthorizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    authorization: str


class OrganizationFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    external_id: Oin = Field(..., description=EXTERNAL_ID_DESCRIPTION)
    name: str = Field(..., description=NAME_DESCRIPTION, examples=["OrganizationName"])
    receive_personal_id_types: list[PersonalIdType] = Field(examples=[[PersonalIdType.OPRF]])
    request_personal_id_types: list[PersonalIdType] = Field(examples=[[PersonalIdType.OPRF]])


class OrganizationCreate(OrganizationFields):
    pass


class OrganizationUpdate(OrganizationFields):
    deleted: bool = Field(examples=[False])


class OrganizationQueryParams(BaseModel):
    external_id: Oin | None = Field(default=None, description=EXTERNAL_ID_DESCRIPTION)
    name: str | None = Field(default=None, description=NAME_DESCRIPTION)
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Organization(OrganizationCreate, BaseReadFields):
    pass
