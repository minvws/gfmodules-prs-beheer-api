from datetime import datetime
from typing import List
from uuid import UUID

from app.db.db import Database
from app.db.models.organization import OrganizationEntity
from app.db.repository.organization import OrganizationRepository


class OrganizationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def get_one(self, id: UUID) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return repo.get_one(id)

    def get_many(self, oin: str | None = None) -> List[OrganizationEntity]:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return list(repo.get_many(oin=oin))

    def create_one(
        self,
        oin: str,
        common_name: str,
        client_certificate: str | None = None,
    ) -> OrganizationEntity:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            entity = OrganizationEntity(
                oin=oin,
                common_name=common_name,
                client_certificate=client_certificate,
            )
            return repo.add_one(entity)

    def delete_one(self, id: UUID) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return repo.update(id, deleted_at=datetime.now())

    def update_one(self, id: UUID, **kwargs: object) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return repo.update(id, **kwargs)
