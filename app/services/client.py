from datetime import datetime
from typing import List
from uuid import UUID

from app import scope_utils
from app.db.db import Database
from app.db.models.client import ClientEntity
from app.db.repository.client import ClientRepository
from app.db.repository.organization import OrganizationRepository
from app.db.session import DbSession
from app.models.oin import Oin
from app.services.exceptions import ScopesNotGrantedError


class ClientService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_one(
        self,
        organization_id: UUID,
        oin: Oin,
        common_name: str,
        mandate_id: str,
        scopes: str | None = None,
    ) -> ClientEntity:
        with self.db.get_db_session() as session:
            self._assert_scopes_granted(session, organization_id, scopes)
            repo = session.get_repository(ClientRepository)
            entity = ClientEntity(
                organization_id=organization_id,
                mandate_id=mandate_id,
                oin=str(oin),
                common_name=common_name,
                scopes=scopes,
            )
            return repo.add_one(entity)

    def get_one(self, id: UUID, organization_id: UUID) -> ClientEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            return repo.get_one(organization_id, id)

    def get_many(
        self,
        organization_id: UUID,
        oin: Oin | None = None,
        common_name: str | None = None,
        mandate_id: str | None = None,
        scopes: str | None = None,
        include_deleted: bool = False,
    ) -> List[ClientEntity]:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            return list(
                repo.get_many(
                    organization_id=organization_id,
                    oin=str(oin) if oin else None,
                    common_name=common_name,
                    mandate_id=mandate_id,
                    scopes=scopes,
                    include_deleted=include_deleted,
                )
            )

    def update_one(self, id: UUID, organization_id: UUID, **kwargs: object) -> ClientEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            if not repo.exists(organization_id, id):
                return None
            if "oin" in kwargs:
                kwargs["oin"] = str(kwargs["oin"])
            if "scopes" in kwargs:
                self._assert_scopes_granted(session, organization_id, kwargs["scopes"])  # type: ignore[arg-type]
            return repo.update(organization_id, id, **kwargs)

    def delete_one(self, id: UUID, organization_id: UUID) -> ClientEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            if not repo.exists(organization_id, id):
                return None
            return repo.update(organization_id, id, deleted_at=datetime.now())

    def resolve(
        self,
        oin: Oin,
        common_name: str,
        mandate_id: str,
    ) -> str | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            result = repo.get_by_credentials(common_name=common_name, oin=str(oin), mandate_id=mandate_id)
            return result.scopes if result is not None else None

    @staticmethod
    def _assert_scopes_granted(session: DbSession, organization_id: UUID, requested: str | None) -> None:
        organization_repo = session.get_repository(OrganizationRepository)
        organization = organization_repo.get_one(organization_id)
        available = organization.scopes if organization is not None else None
        if not scope_utils.is_subset(requested, available):
            ungranted = scope_utils.parse(requested) - scope_utils.parse(available)
            raise ScopesNotGrantedError(ungranted)
