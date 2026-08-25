from pydantic import BaseModel, ConfigDict, Field

from app.models.base import INCLUDE_DELETED_DESCRIPTION, BaseReadFields


class CertificateFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_identifier: str
    domain: str


class CertificateQueryParams(BaseModel):
    include_deleted: bool = Field(default=False, description=INCLUDE_DELETED_DESCRIPTION)


class Certificate(CertificateFields, BaseReadFields):
    pass
