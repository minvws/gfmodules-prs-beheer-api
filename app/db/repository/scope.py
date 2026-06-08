from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.db.decorator import repository
from app.db.models.scope import ScopeEntity
from app.db.repository.base import RepositoryBase


@repository(ScopeEntity)
class ScopeRepository(RepositoryBase):
    def add_one(self, data: ScopeEntity) -> ScopeEntity:
        try:
            self.db_session.add(data)
            self.db_session.commit()
            return data
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_one(self, id: UUID) -> ScopeEntity | None:
        stmt = select(ScopeEntity).where(ScopeEntity.id == id)
        return self.db_session.session.execute(stmt).scalar()

    def get_by_name(self, name: str) -> ScopeEntity | None:
        stmt = select(ScopeEntity).where(ScopeEntity.name == name)
        return self.db_session.session.execute(stmt).scalar()

    def get_many(self, active_only: bool = False) -> Sequence[ScopeEntity]:
        stmt = select(ScopeEntity)
        if active_only:
            stmt = stmt.where(ScopeEntity.active.is_(True))
        return self.db_session.session.execute(stmt).scalars().all()

    def update(self, id: UUID, **kwargs: object) -> ScopeEntity | None:
        try:
            target = {k: kwargs[k] for k in ScopeEntity.__table__.columns.keys() if k in kwargs}
            if not target:
                return None
            stmt = update(ScopeEntity).where(ScopeEntity.id == id).values(target).returning(ScopeEntity)
            result = self.db_session.session.execute(stmt).scalar_one_or_none()
            self.db_session.commit()
            return result
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
