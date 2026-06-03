from datetime import datetime
from typing import List
from uuid import UUID

from app.db.db import Database
from app.db.models.client import ClientEntity
from app.db.repository.client import ClientRepository
from app.models.oin import Oin


class ClientService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_one(self, id: UUID, organization_id: UUID) -> ClientEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            return repo.get_one(id, organization_id)

    def get_many(self, organization_id: UUID, oin: Oin | None = None) -> List[ClientEntity]:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            return list(repo.get_many(organization_id=organization_id, oin=str(oin) if oin else None))

    def create_one(
        self,
        organization_id: UUID,
        oin: Oin,
        common_name: str,
        certificate: str | None = None,
        allowed_scopes: str | None = None,
    ) -> ClientEntity:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            entity = ClientEntity(
                organization_id=organization_id,
                oin=str(oin),
                common_name=common_name,
                certificate=certificate,
                allowed_scopes=allowed_scopes,
            )
            return repo.add_one(entity)

    def delete_one(self, id: UUID, organization_id: UUID) -> ClientEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            return repo.update(id, organization_id, deleted_at=datetime.now())

    def update_one(self, id: UUID, organization_id: UUID, **kwargs: object) -> ClientEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            return repo.update(id, organization_id, **kwargs)
