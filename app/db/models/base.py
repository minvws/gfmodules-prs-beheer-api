from typing import Any
from datetime import datetime, timezone
from sqlalchemy import MetaData, DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

admin_metadata_obj = MetaData(schema="admin")

prs_metadata_obj = MetaData(schema="prs")


class Base:
    pass


class AdminBase(Base, DeclarativeBase):
    metadata = admin_metadata_obj


class PrsBase(Base, DeclarativeBase):
    metadata = prs_metadata_obj


class WithTimestamps:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(tz=timezone.utc),
    )
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }
