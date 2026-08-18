from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.db.decorator import repository
from app.db.models.organization import OrganizationEntity
from app.db.repository.base import RepositoryBase
from app.models.oin import Oin


@repository(OrganizationEntity)
class OrganizationRepository(RepositoryBase):
    def add_one(self, data: OrganizationEntity) -> OrganizationEntity:
        try:
            self.db_session.add(data)
            self.db_session.commit()
            return data
        except SQLAlchemyError:
            self.db_session.rollback()
            raise

    def get_one(self, id: UUID) -> OrganizationEntity | None:
        stmt = select(OrganizationEntity).where(OrganizationEntity.id == id)
        return self.db_session.session.execute(stmt).scalar()

    def get_one_with_clients(self, id: UUID) -> OrganizationEntity | None:
        """Fetch an organization with its clients eagerly loaded (the relationship
        is ``lazy="raise"``). Includes soft-deleted clients; filter on ``deleted_at``."""
        stmt = select(OrganizationEntity).options(selectinload(OrganizationEntity.clients)).where(self._and_clause(id))
        return self.db_session.session.execute(stmt).scalar()

    def exists(self, id: UUID) -> bool:
        stmt = select(select(OrganizationEntity.id).where(self._and_clause(id)).exists())
        return bool(self.db_session.session.execute(stmt).scalar())

    def get_one_by_register_id(self, register_id: Oin) -> OrganizationEntity | None:
        stmt = select(OrganizationEntity).where(
            and_(
                OrganizationEntity.register_id == register_id,
                OrganizationEntity.inactive_at.is_(None),
            )
        )
        return self.db_session.session.execute(stmt).scalar()

    def get_many(
        self,
        register_id: Oin | None = None,
        name: str | None = None,
        scopes: Any | None = None,
        include_deleted: bool = False,
    ) -> Sequence[OrganizationEntity]:
        conditions: list[ColumnElement[bool]] = []
        if not include_deleted:
            conditions.append(OrganizationEntity.deleted_at.is_(None))
        if register_id:
            conditions.append(OrganizationEntity.register_id == register_id)
        if name:
            conditions.append(OrganizationEntity.name == name)
        stmt = select(OrganizationEntity)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        return self.db_session.session.execute(stmt).scalars().all()

    def _and_clause(self, id: UUID) -> ColumnElement[bool]:
        return and_(
            OrganizationEntity.id == id,
            OrganizationEntity.deleted_at.is_(None),
        )
