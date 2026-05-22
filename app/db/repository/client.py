from typing import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, and_, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.db.decorator import repository
from app.db.models.client import ClientEntity
from app.db.repository.base import RepositoryBase


@repository(ClientEntity)
class ClientRepository(RepositoryBase):
    def add_one(self, data: ClientEntity) -> ClientEntity:
        try:
            self.db_session.add(data)
            self.db_session.commit()
            return data
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_one(self, id: UUID, organization_id: UUID) -> ClientEntity | None:
        stmt = select(ClientEntity).where(
            and_(
                ClientEntity.id == id,
                ClientEntity.organization_id == organization_id,
                ClientEntity.deleted_at.is_(None),
            )
        )
        return self.db_session.session.execute(stmt).scalar()

    def get_many(self, organization_id: UUID, oin: str | None = None) -> Sequence[ClientEntity]:
        conditions: list[ColumnElement[bool]] = [
            ClientEntity.organization_id == organization_id,
            ClientEntity.deleted_at.is_(None),
        ]
        if oin:
            conditions.append(ClientEntity.oin == oin)

        stmt = select(ClientEntity).where(and_(*conditions))
        return self.db_session.session.execute(stmt).scalars().all()

    def update(self, id: UUID, organization_id: UUID, **kwargs: object) -> ClientEntity | None:
        try:
            target = {k: kwargs[k] for k in ClientEntity.__table__.columns.keys() if k in kwargs}
            if not target:
                return None

            stmt = (
                update(ClientEntity)
                .where(
                    and_(
                        ClientEntity.id == id,
                        ClientEntity.organization_id == organization_id,
                        ClientEntity.deleted_at.is_(None),
                    )
                )
                .values(target)
                .returning(ClientEntity)
            )

            result = self.db_session.session.execute(stmt).scalar_one_or_none()
            self.db_session.commit()
            return result
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e
