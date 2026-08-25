import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException

from app.db.db import Database
from app.db.models.organization import OrganizationEntity
from app.db.repository.organization import OrganizationRepository
from app.db.repository.personal_id_type import PersonalIdTypeRepository
from app.models.oin import Oin
from app.models.organization import Organization, OrganizationCreate, OrganizationUpdate

logger = logging.getLogger(__name__)


class OrganizationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_one(self, input: OrganizationCreate) -> Organization:
        with self.db.get_db_session(commit=True) as session:
            repo = session.get_repository(OrganizationRepository)
            personal_id_type_repo = session.get_repository(PersonalIdTypeRepository)
            receive_personal_id_types = personal_id_type_repo.get_many(
                [str(e) for e in input.receive_personal_id_types]
            )
            if len(receive_personal_id_types) != len(input.receive_personal_id_types):
                raise HTTPException(status_code=404, detail="Not all of provided receive personal_id_types exists")
            request_personal_id_types = personal_id_type_repo.get_many(
                [str(e) for e in input.request_personal_id_types]
            )
            if len(request_personal_id_types) != len(input.request_personal_id_types):
                raise HTTPException(status_code=404, detail="Not all of provided request personal_id_types exists")
            entity: OrganizationEntity = repo.add_one(
                OrganizationEntity(
                    external_id=input.external_id,
                    name=input.name,
                    receive_personal_id_types=receive_personal_id_types,
                    request_personal_id_types=request_personal_id_types,
                )
            )
            session.flush()
            return Organization(**entity.to_dict())

    def get_one(self, id: UUID) -> Organization:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            entity = repo.get_one(id)
            if not entity:
                raise HTTPException(status_code=404, detail="Organization not found")
            return Organization(**entity.to_dict())

    def get_many(
        self,
        external_id: Oin | None = None,
        name: str | None = None,
        include_deleted: bool = False,
    ) -> list[Organization]:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            entities = repo.get_many(external_id=external_id, name=name, include_deleted=include_deleted)

            return [Organization(**entity.to_dict()) for entity in entities]

    def update_one(self, id: UUID, organization_update: OrganizationUpdate) -> Organization:
        with self.db.get_db_session(commit=True) as session:
            repo = session.get_repository(OrganizationRepository)
            personal_id_type_repo = session.get_repository(PersonalIdTypeRepository)
            organization_entity = repo.get_one(id)
            if not organization_entity:
                logger.debug("Organization not found for update id=%s", id)
                raise HTTPException(status_code=404, detail="Organization not found")
            now = datetime.now(timezone.utc)
            organization_entity.external_id = organization_update.external_id
            organization_entity.name = organization_update.name
            organization_entity.updated_at = now
            if organization_entity.deleted_at and not organization_update.deleted:
                organization_entity.deleted_at = None
            if not organization_entity.deleted_at and organization_update.deleted:
                organization_entity.deleted_at = now

            receive_personal_id_types = personal_id_type_repo.get_many(organization_update.receive_personal_id_types)
            if len(receive_personal_id_types) != len(organization_update.receive_personal_id_types):
                raise HTTPException(status_code=404, detail="Not all of provided receive personal_id_types exists")

            request_personal_id_types = personal_id_type_repo.get_many(organization_update.request_personal_id_types)
            if len(request_personal_id_types) != len(organization_update.request_personal_id_types):
                raise HTTPException(status_code=404, detail="Not all of provided request personal_id_types exists")

            organization_entity.receive_personal_id_types = list(receive_personal_id_types)
            organization_entity.request_personal_id_types = list(request_personal_id_types)

            return Organization(**organization_entity.to_dict())

    def delete_one(self, id: UUID) -> Organization:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            entity = repo.get_one(id)
            if not entity:
                logger.debug("Organization not found for update id=%s", id)
                raise HTTPException(status_code=404)
            if [client for client in entity.clients if client.deleted_at is None]:
                logger.debug("Organization still has active clients")
                raise HTTPException(status_code=403, detail="Organization still has active clients")
            entity.updated_at = entity.deleted_at = datetime.now(tz=timezone.utc)
            ret_value = Organization(**entity.to_dict())
            session.commit()
            return ret_value
