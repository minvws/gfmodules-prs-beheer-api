
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

admin_metadata_obj = MetaData(schema="admin")

prs_metadata_obj = MetaData(schema="prs")


class Base:
    pass


class AdminBase(Base, DeclarativeBase):
    metadata = admin_metadata_obj


class PrsBase(Base, DeclarativeBase):
    metadata = prs_metadata_obj
