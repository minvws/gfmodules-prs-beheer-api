from pydantic import BaseModel, ConfigDict, Field

from app.models.base import INCLUDE_DELETED_DESCRIPTION, Base
from app.models.oin import Oin

REGISTER_ID_DESCRIPTION = "The OIN of the organization"
NAME_DESCRIPTION = "The name of the organization"
SCOPES_DESCRIPTION = "The space separated scopes granted to the organization"


class OrganizationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    register_id: Oin = Field(..., description=REGISTER_ID_DESCRIPTION)
    name: str = Field(..., description=NAME_DESCRIPTION)
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, description=NAME_DESCRIPTION)
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)


class OrganizationQueryParams(BaseModel):
    register_id: Oin | None = Field(default=None, description=REGISTER_ID_DESCRIPTION)
    name: str | None = Field(default=None, description=NAME_DESCRIPTION)
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Organization(Base, OrganizationCreate):
    pass
