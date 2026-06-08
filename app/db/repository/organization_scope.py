from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.db.decorator import repository
from app.db.models.organization_scope import OrganizationScopeEntity
from app.db.repository.base import RepositoryBase


@repository(OrganizationScopeEntity)
class OrganizationScopeRepository(RepositoryBase):
    def add(self, organization_id: UUID, scope_id: UUID) -> OrganizationScopeEntity:
        try:
            entity = OrganizationScopeEntity(organization_id=organization_id, scope_id=scope_id)
            self.db_session.add(entity)
            self.db_session.commit()
            return entity
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def remove(self, organization_id: UUID, scope_id: UUID) -> None:
        try:
            stmt = delete(OrganizationScopeEntity).where(
                and_(
                    OrganizationScopeEntity.organization_id == organization_id,
                    OrganizationScopeEntity.scope_id == scope_id,
                )
            )
            self.db_session.session.execute(stmt)
            self.db_session.commit()
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_scope_ids_for_org(self, organization_id: UUID) -> Sequence[UUID]:
        stmt = select(OrganizationScopeEntity.scope_id).where(
            OrganizationScopeEntity.organization_id == organization_id
        )
        return self.db_session.session.execute(stmt).scalars().all()

    def has_scope(self, organization_id: UUID, scope_id: UUID) -> bool:
        stmt = select(OrganizationScopeEntity).where(
            and_(
                OrganizationScopeEntity.organization_id == organization_id,
                OrganizationScopeEntity.scope_id == scope_id,
            )
        )
        return self.db_session.session.execute(stmt).scalar() is not None
