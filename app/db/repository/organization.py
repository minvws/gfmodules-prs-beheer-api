from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, and_, select
from sqlalchemy.orm import selectinload

from app.db.models.organization import OrganizationEntity
from app.db.repository.base import RepositoryBase
from app.models.oin import Oin


class OrganizationRepository(RepositoryBase):
    def add_one(self, data: OrganizationEntity) -> OrganizationEntity:
        self.db_session.add(data)
        return data

    def get_one(self, id: UUID) -> OrganizationEntity | None:
        stmt = select(OrganizationEntity).where(OrganizationEntity.id == id)
        return self.db_session.session.execute(stmt).scalar()

    def get_one_with_clients(self, id: UUID) -> OrganizationEntity | None:
        """Fetch an organization with its clients eagerly loaded (the relationship
        is ``lazy="raise"``). Includes soft-deleted clients; filter on ``deleted_at``."""
        stmt = select(OrganizationEntity).options(selectinload(OrganizationEntity.clients)).where(self._and_clause(id))
        return self.db_session.session.execute(stmt).scalar()

    def get_many(
        self,
        external_id: Oin | None = None,
        name: str | None = None,
        include_deleted: bool = False,
    ) -> Sequence[OrganizationEntity]:
        conditions: list[ColumnElement[bool]] = []
        if not include_deleted:
            conditions.append(OrganizationEntity.deleted_at.is_(None))
        if external_id:
            conditions.append(OrganizationEntity.external_id == external_id)
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
