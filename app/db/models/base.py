from enum import StrEnum

from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

admin_metadata_obj = MetaData(schema="admin")
AdminBase = declarative_base(metadata=admin_metadata_obj)

prs_metadata_obj = MetaData(schema="admin")
PrsBase = declarative_base(metadata=prs_metadata_obj)


class PersonalIdType(StrEnum):
    OPRF = "oprf"


# receive_authorization_association_table = Table(
#    "receive_authorizations",
#    Base.metadata,
#    Column("organization_id", ForeignKey("admin.organizations.id"), primary_key=True),
#    Column("authorization_id", ForeignKey("prs.authorizations.id"), primary_key=True),
#    schema="prs",
# )
