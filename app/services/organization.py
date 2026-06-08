from datetime import datetime
from typing import List
from uuid import UUID

from app.db.db import Database
from app.db.models.organization import OrganizationEntity
from app.db.repository.organization import OrganizationRepository
from app.models.oin import Oin


class OrganizationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    @staticmethod
    def _apply_legacy_aliases(entity: OrganizationEntity) -> OrganizationEntity:
        # Keep legacy API/model field names available while services migrate.
        entity.oin = entity.register_id  # type: ignore
        entity.common_name = entity.name  # type: ignore
        entity.client_certificate = None  # type: ignore
        return entity

    def get_one(self, id: UUID) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            result = repo.get_one(id)
            if result is None:
                return None
            return self._apply_legacy_aliases(result)

    def get_many(self, oin: Oin | None = None) -> List[OrganizationEntity]:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return [
                self._apply_legacy_aliases(entity) for entity in repo.get_many(register_id=str(oin) if oin else None)
            ]

    def create_one(
        self,
        oin: Oin,
        common_name: str,
        client_certificate: str | None = None,
    ) -> OrganizationEntity:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            entity = OrganizationEntity(
                register_id=str(oin),
                name=common_name,
            )
            return self._apply_legacy_aliases(repo.add_one(entity))

    def delete_one(self, id: UUID) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            result = repo.update(id, deleted_at=datetime.now())
            if result is None:
                return None
            return self._apply_legacy_aliases(result)

    def update_one(self, id: UUID, **kwargs: object) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            translated = dict(kwargs)
            translated.pop("client_certificate", None)
            if "common_name" in translated:
                translated["name"] = translated.pop("common_name")
            if "oin" in translated:
                translated["register_id"] = translated.pop("oin")
            result = repo.update(id, **translated)
            if result is None:
                return None
            return self._apply_legacy_aliases(result)
