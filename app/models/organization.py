from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.container import get_allowed_scopes
from app.models.base import INCLUDE_DELETED_DESCRIPTION, Base
from app.models.oin import Oin
from app.scope_utils import check_in_configured_scopes

REGISTER_ID_DESCRIPTION = "The OIN of the organization"
NAME_DESCRIPTION = "The name of the organization"
SCOPES_DESCRIPTION = "The space separated scopes granted to the organization"


class Scopes(BaseModel):
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)

    @field_validator("scopes", mode="before")
    @classmethod
    def is_allowed(cls, value: str | None) -> str | None:
        allowed_scopes = get_allowed_scopes()
        if not check_in_configured_scopes(allowed_scopes, value):
            supported = " ".join(sorted(allowed_scopes))
            raise ValueError(f"Requested scopes {value} are not allowed. Supported scopes are {supported}")
        return value


class OrganizationCreate(Scopes):
    model_config = ConfigDict(from_attributes=True)

    register_id: Oin = Field(..., description=REGISTER_ID_DESCRIPTION)
    name: str = Field(..., description=NAME_DESCRIPTION)


class OrganizationUpdate(Scopes):
    name: str | None = Field(default=None, description=NAME_DESCRIPTION)


class OrganizationQueryParams(BaseModel):
    register_id: Oin | None = Field(default=None, description=REGISTER_ID_DESCRIPTION)
    name: str | None = Field(default=None, description=NAME_DESCRIPTION)
    scopes: str | None = Field(default=None, description=SCOPES_DESCRIPTION)
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Organization(Base, OrganizationCreate):
    pass
