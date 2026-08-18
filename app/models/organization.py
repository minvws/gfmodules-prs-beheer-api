from app.db.models.base import PersonalIdType
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.base import INCLUDE_DELETED_DESCRIPTION, Base
from app.models.oin import Oin

REGISTER_ID_DESCRIPTION = "The OIN of the organization"
NAME_DESCRIPTION = "The name of the organization"
SCOPES_DESCRIPTION = "The space separated scopes granted to the organization"


class OrganizationRequestAuthorizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    authorization: str


class OrganizationReadFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class OrganizationFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    external_id: Oin = Field(..., description=REGISTER_ID_DESCRIPTION)
    name: str = Field(..., description=NAME_DESCRIPTION, example="OrganizationName")
    receive_personal_id_types: list[PersonalIdType] = Field(example=[PersonalIdType.OPRF])
    request_personal_id_types: list[PersonalIdType] = Field(example=[PersonalIdType.OPRF])


class OrganizationCreate(OrganizationFields):
    pass


class OrganizationUpdate(OrganizationFields):
    deleted: bool = Field(example=False)


class OrganizationQueryParams(BaseModel):
    register_id: Oin | None = Field(default=None, description=REGISTER_ID_DESCRIPTION)
    name: str | None = Field(default=None, description=NAME_DESCRIPTION)
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Organization(OrganizationReadFields, OrganizationCreate):
    pass
