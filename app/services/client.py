from app.db.session import DbSession
from app.models.organization import Organization
from app.db.repository.organization import OrganizationRepository
from app.db.models.client_request_personal_id_type import ClientRequestPersonalIdTypeEntity
from app.models.client import Client, ClientCreate, ClientUpdate
from fastapi import HTTPException
import logging
from datetime import datetime, timezone
from uuid import UUID

from app.db.db import Database
from app.db.models.client import ClientEntity
from app.db.repository.client import ClientRepository
from app.models.oin import Oin
from app.services.organization import OrganizationService

logger = logging.getLogger(__name__)


class ClientService:
    def __init__(
        self,
        db: Database,
    ) -> None:
        self.db = db

    def _get_organization_or_404(self, session: DbSession, organization_id: UUID) -> OrganizationEntity:
        logger.debug("Checking if organization %s exists", organization_id)
        org_repo: OrganizationRepository = session.get_repository(OrganizationRepository)
        organization = org_repo.get_one(organization_id)
        if not organization:
            logger.debug("Organization %s not found", organization_id)
            raise HTTPException(status_code=404, detail="Organization not found.")
        return organization

    def create_one(
        self,
        organization_id: UUID,
        input: ClientCreate,
    ) -> Client:
        with self.db.get_db_session() as session:
            organization = self._get_organization_or_404(session, organization_id)

            request_by_pid = {item.personal_id_type: item for item in organization.request_personal_id_types}
            not_in_organization = [pid for pid in input.request_personal_id_types if pid not in request_by_pid]
            if not_in_organization:
                raise HTTPException(
                    status_code=404,
                    detail=f"The following Personal id types do not exist in the organization: {', '.join(not_in_organization)}",
                )

            repo: ClientRepository = session.get_repository(ClientRepository)
            entity = ClientEntity(
                organization_id=organization_id,
                external_id=input.external_id,
                common_name=input.common_name,
                request_personal_id_types=[
                    ClientRequestPersonalIdTypeEntity(
                        organization_request_personal_id_type=request_by_pid[personal_id_type],
                    )
                    for personal_id_type in input.request_personal_id_types
                ],
            )
            entity = repo.add_one(entity)
            session.commit()
            return Client(**entity.to_dict())

    def get_one(self, id: UUID, organization_id: UUID) -> Client | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            entity = repo.get_one(organization_id, id)
            return Client(**entity.to_dict()) if entity else None

    def get_many(
        self,
        organization_id: UUID,
        external_id: Oin | None = None,
        common_name: str | None = None,
        include_deleted: bool = False,
    ) -> list[Client]:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            entities = repo.get_many(
                organization_id=organization_id,
                external_id=external_id,
                common_name=common_name,
                include_deleted=include_deleted,
            )

            return [Client(**entity.to_dict()) for entity in entities]

    def update_one(self, id: UUID, organization_id, update: ClientUpdate) -> Client:
        with self.db.get_db_session() as session:
            organization = self._get_organization_or_404(session, organization_id)

            request_by_pid = {item.personal_id_type: item for item in organization.request_personal_id_types}
            not_in_organization = [pid for pid in update.request_personal_id_types if pid not in request_by_pid]
            if not_in_organization:
                raise HTTPException(
                    status_code=404,
                    detail=f"The following Personal id types do not exist in the organization: {', '.join(not_in_organization)}",
                )

            repo = session.get_repository(ClientRepository)
            client_entity: ClientEntity = repo.get_one(organization_id, id)
            if not client_entity:
                logger.debug("Client not found for update organization_id%s, id=%s", organization_id, id)
                raise HTTPException(status_code=404)
            client_entity.updated_at = datetime.now(tz=timezone.utc)
            client_entity.external_id = update.external_id
            client_entity.common_name = update.common_name
            ClientService.update_request_personal_id_types(client_entity, update, request_by_pid)
            session.commit()
            return Client(**client_entity.to_dict())

    @staticmethod
    def update_request_personal_id_types(
        client_entity: ClientEntity,
        client_update: ClientUpdate,
        request_by_pid: dict[str, OrganiztionRequestPersonalIdTypeEntity],
    ):
        current = set(
            [
                _type.organization_request_personal_id_type.personal_id_type
                for _type in client_entity.request_personal_id_types
            ]
        )
        updated = set(client_update.request_personal_id_types)

        to_add = updated - current
        to_remove = [
            e
            for e in client_entity.request_personal_id_types
            if e.organization_request_personal_id_type.personal_id_type not in updated
        ]

        for entry in to_add:
            client_entity.request_personal_id_types.append(
                ClientRequestPersonalIdTypeEntity(organization_request_personal_id_type=request_by_pid[entry])
            )

        for entry in to_remove:
            client_entity.request_personal_id_types.remove(entry)

    def delete_one(self, id: UUID, organization_id: UUID) -> Client:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            client_entity: ClientEntity = repo.get_one(organization_id, id)
            if not client_entity:
                logger.debug("Client not found for update organization_id%s, id=%s", organization_id, id)
                raise HTTPException(status_code=404)
            client_entity.deleted_at = client_entity.updated_at = datetime.now(tz=timezone.utc)
            session.commit()
            return Client(**client_entity.to_dict())

    def resolve(
        self,
        oin: Oin,
        common_name: str,
        register_id: Oin,
    ) -> ClientEntity | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            return repo.get_by_credentials(common_name=common_name, oin=oin, register_id=register_id)
