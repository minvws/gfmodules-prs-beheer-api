import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException

from app.db.db import Database
from app.db.models.client import ClientEntity
from app.db.models.organization import OrganizationEntity
from app.db.models.organization_personal_id_type import ClientPersonalIdTypeEntity
from app.db.repository.certificate import CertificateRepository
from app.db.repository.client import ClientRepository
from app.db.repository.organization import OrganizationRepository
from app.db.session import DbSession
from app.models.client import (
    Client,
    ClientCreate,
    ClientQueryParams,
    ClientUpdate,
    ResolveRequest,
    ResolveResponse,
)

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
            raise HTTPException(status_code=404, detail="Organization not found")
        return organization

    def create_one(
        self,
        organization_id: UUID,
        input: ClientCreate,
    ) -> Client:
        with self.db.get_db_session() as session:
            organization = self._get_organization_or_404(session, organization_id)

            request_by_pid = {item.name: item for item in organization.request_personal_id_types}
            not_in_organization = [pid for pid in input.request_personal_id_types if pid not in request_by_pid]
            if not_in_organization:
                raise HTTPException(
                    status_code=404,
                    detail=f"The following Personal id types do not exist in the organization: {', '.join(not_in_organization)}",
                )
            cert_repo = session.get_repository(CertificateRepository)
            certificates = cert_repo.get_many(organization_id, input.certificates)

            repo = session.get_repository(ClientRepository)
            entity = ClientEntity(
                organization_id=organization_id,
                request_personal_id_types=[
                    ClientPersonalIdTypeEntity(
                        personal_id_type_id=request_by_pid[personal_id_type].id,
                        organization_id=organization.id,
                    )
                    for personal_id_type in input.request_personal_id_types
                ],
                certificates=list(certificates),
            )
            entity = repo.add_one(entity)
            session.commit()
            return Client(**entity.to_dict())

    def get_one(self, id: UUID, organization_id: UUID) -> Client:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            entity = repo.get_one(organization_id, id)
            if not entity:
                raise HTTPException(status_code=404, detail="Client not found")
            return Client(**entity.to_dict())

    def get_many(self, organization_id: UUID, client_query_params: ClientQueryParams) -> list[Client]:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            entities = repo.get_many(
                organization_id=organization_id,
                include_deleted=client_query_params.include_deleted,
            )

            return [Client(**entity.to_dict()) for entity in entities]

    def update_one(self, id: UUID, organization_id: UUID, update: ClientUpdate) -> Client:
        with self.db.get_db_session(commit=True) as session:
            organization = self._get_organization_or_404(session, organization_id)
            organization_pids = [pide.name for pide in organization.request_personal_id_types]

            not_in_organization = [pid for pid in update.request_personal_id_types if pid not in organization_pids]
            if not_in_organization:
                raise HTTPException(
                    status_code=404,
                    detail=f"The following Personal id types do not exist in the organization: {', '.join(not_in_organization)}",
                )

            cert_repo = session.get_repository(CertificateRepository)
            certificates = list(cert_repo.get_many(organization_id, update.certificates))
            repo = session.get_repository(ClientRepository)
            client_entity = repo.get_one(organization_id, id)
            if not client_entity:
                logger.debug("Client not found for update organization_id%s, id=%s", organization_id, id)
                raise HTTPException(status_code=404, detail="Client not found")
            now = datetime.now(timezone.utc)
            client_entity.updated_at = now
            client_entity.certificates = certificates
            if client_entity.deleted_at and not update.deleted:
                client_entity.deleted_at = None
            if not client_entity.deleted_at and update.deleted:
                client_entity.deleted_at = now

            updated = [
                ClientPersonalIdTypeEntity(personal_id_type=rpit, organization_id=organization.id)
                for rpit in organization.request_personal_id_types
                if rpit.name in update.request_personal_id_types
            ]
            client_entity.request_personal_id_types = updated
            return Client(**client_entity.to_dict())

    def delete_one(self, id: UUID, organization_id: UUID) -> Client:
        with self.db.get_db_session() as session:
            repo = session.get_repository(ClientRepository)
            client_entity = repo.get_one(organization_id, id)
            if not client_entity:
                logger.debug("Client not found for update organization_id%s, id=%s", organization_id, id)
                raise HTTPException(status_code=404)
            client_entity.deleted_at = client_entity.updated_at = datetime.now(tz=timezone.utc)
            session.commit()
            return Client(**client_entity.to_dict())

    def resolve(self, resolve_request: ResolveRequest) -> ResolveResponse:
        with self.db.get_db_session() as session:
            client_repo = session.get_repository(ClientRepository)
            entities = client_repo.get_many(
                client_id=resolve_request.client_id,
                organization_external_id=resolve_request.organization_external_id,
                certificate_domain=resolve_request.certificate_domain,
                certificate_organization_identifier=resolve_request.certificate_organization_identifier,
            )
            if resolve_request.client_id is not None and len(entities) > 1:
                logger.error("It should not be possible to have multiple clients for a single client id")
                raise HTTPException(status_code=500, detail="Internal Server Error")
            if not entities:
                raise HTTPException(status_code=404, detail="Client authorization does not exist for given parameters")
            entity = entities[0]
            return ResolveResponse(
                organization_name=entity.organization.name,
                scopes=" ".join(
                    ["prs:" + str(rpit.personal_id_type.name) for rpit in entity.request_personal_id_types]
                ),
            )
