from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, String, Uuid, func, Column, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# receive_authorization_association_table = Table(
#    "receive_authorizations",
#    Base.metadata,
#    Column("organization_id", ForeignKey("admin.organizations.id"), primary_key=True),
#    Column("authorization_id", ForeignKey("prs.authorizations.id"), primary_key=True),
#    schema="prs",
# )
