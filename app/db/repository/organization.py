from typing import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, and_, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.db.decorator import repository
from app.db.models.organization import OrganizationEntity
from app.db.repository.base import RepositoryBase


@repository(OrganizationEntity)
class OrganizationRepository(RepositoryBase):
    def add_one(self, data: OrganizationEntity) -> OrganizationEntity:
        try:
            self.db_session.add(data)
            self.db_session.commit()
            return data
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_one(self, id: UUID) -> OrganizationEntity | None:
        stmt = select(OrganizationEntity).where(
            and_(
                OrganizationEntity.id == id,
                OrganizationEntity.deleted_at.is_(None),
            )
        )
        return self.db_session.session.execute(stmt).scalar()

    def get_many(self, oin: str | None = None) -> Sequence[OrganizationEntity]:
        conditions: list[ColumnElement[bool]] = [OrganizationEntity.deleted_at.is_(None)]
        if oin:
            conditions.append(OrganizationEntity.oin == oin)

        stmt = select(OrganizationEntity).where(and_(*conditions))
        return self.db_session.session.execute(stmt).scalars().all()

    def update(self, id: UUID, **kwargs: object) -> OrganizationEntity | None:
        try:
            target = {k: kwargs[k] for k in OrganizationEntity.__table__.columns.keys() if k in kwargs}
            if not target:
                return None

            stmt = (
                update(OrganizationEntity)
                .where(
                    and_(
                        OrganizationEntity.id == id,
                        OrganizationEntity.deleted_at.is_(None),
                    )
                )
                .values(target)
                .returning(OrganizationEntity)
            )

            result = self.db_session.session.execute(stmt).scalar_one_or_none()
            self.db_session.commit()
            return result
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
