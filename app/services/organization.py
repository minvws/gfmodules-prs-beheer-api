import logging
from datetime import datetime
from typing import List
from uuid import UUID

from app import scope_utils
from app.db.db import Database
from app.db.models.organization import OrganizationEntity
from app.db.repository.client import ClientRepository
from app.db.repository.organization import OrganizationRepository
from app.db.session import DbSession
from app.models.oin import Oin
from app.services.exceptions import OrganizationHasClientsError, ScopesInUseError, ScopesNotGrantedError

logger = logging.getLogger(__name__)


class OrganizationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_one(
        self,
        register_id: Oin,
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
        register_id: Oin | None = None,
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
            if "scopes" in kwargs:
                self._assert_removed_scopes_unused(session, id, kwargs["scopes"])  # type: ignore[arg-type]
            return repo.update(id, **kwargs)

    def _assert_removed_scopes_unused(self, session: DbSession, id: UUID, new_scopes: str | None) -> None:
        repo = session.get_repository(OrganizationRepository)
        current = repo.get_one(id)
        if current is None:
            return
        removed = scope_utils.parse(current.scopes) - scope_utils.parse(new_scopes)
        if not removed:
            return
        client_repo = session.get_repository(ClientRepository)
        in_use = removed & {
            scope for client in client_repo.get_many(organization_id=id) for scope in scope_utils.parse(client.scopes)
        }
        if in_use:
            logger.warning(
                "Cannot remove scopes still in use by clients organization_id=%s scopes=%s",
                id,
                sorted(in_use),
            )
            raise ScopesInUseError(in_use)

    def delete_one(self, id: UUID) -> OrganizationEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            client_repo = session.get_repository(ClientRepository)
            if client_repo.get_many(organization_id=id):
                logger.warning("Cannot delete organization with active clients organization_id=%s", id)
                raise OrganizationHasClientsError()
            return repo.update(id, deleted_at=datetime.now())

    def assert_scopes_granted(self, organization_id: UUID, requested: str | None) -> None:
        organization = self.get_one(organization_id)
        available = organization.scopes if organization is not None else None
        if not scope_utils.is_subset(requested, available):
            ungranted = scope_utils.parse(requested) - scope_utils.parse(available)
            logger.warning(
                "Requested scopes not granted organization_id=%s missing=%s",
                organization_id,
                sorted(ungranted),
            )
            raise ScopesNotGrantedError(ungranted)
