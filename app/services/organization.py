from datetime import datetime
from typing import List
from uuid import UUID

from app.db.db import Database
from app.db.models.organization import OrganizationEntity
from app.db.repository.organization import OrganizationRepository


class OrganizationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_one(
        self,
        register_id: str,
        name: str,
        scopes: str | None = None,
    ) -> OrganizationEntity:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            entity = OrganizationEntity(register_id=register_id, name=name, scopes=scopes)
            return repo.add_one(entity)

    def get_one(self, id: UUID) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return repo.get_one(id)

    def exists(self, id: UUID) -> bool:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return repo.exists(id)

    def get_many(
        self,
        register_id: str | None = None,
        name: str | None = None,
        scopes: str | None = None,
        include_deleted: bool = False,
    ) -> List[OrganizationEntity]:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return list(
                repo.get_many(register_id=register_id, name=name, scopes=scopes, include_deleted=include_deleted)
            )

    def update_one(self, id: UUID, **kwargs: object) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return repo.update(id, **kwargs)

    def delete_one(self, id: UUID) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return repo.update(id, deleted_at=datetime.now())
