from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.db.decorator import repository
from app.db.models.client_scope import ClientScopeEntity
from app.db.repository.base import RepositoryBase


@repository(ClientScopeEntity)
class ClientScopeRepository(RepositoryBase):
    def add(self, client_id: UUID, scope_id: UUID) -> ClientScopeEntity:
        try:
            entity = ClientScopeEntity(client_id=client_id, scope_id=scope_id)
            self.db_session.add(entity)
            self.db_session.commit()
            return entity
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def remove(self, client_id: UUID, scope_id: UUID) -> None:
        try:
            stmt = delete(ClientScopeEntity).where(
                and_(
                    ClientScopeEntity.client_id == client_id,
                    ClientScopeEntity.scope_id == scope_id,
                )
            )
            self.db_session.session.execute(stmt)
            self.db_session.commit()
        except SQLAlchemyError as e:
            self.db_session.rollback()
            raise e

    def get_scope_ids_for_client(self, client_id: UUID) -> Sequence[UUID]:
        stmt = select(ClientScopeEntity.scope_id).where(ClientScopeEntity.client_id == client_id)
        return self.db_session.session.execute(stmt).scalars().all()

    def has_scope(self, client_id: UUID, scope_id: UUID) -> bool:
        stmt = select(ClientScopeEntity).where(
            and_(
                ClientScopeEntity.client_id == client_id,
                ClientScopeEntity.scope_id == scope_id,
            )
        )
        return self.db_session.session.execute(stmt).scalar() is not None
