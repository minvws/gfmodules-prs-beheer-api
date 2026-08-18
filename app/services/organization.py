from app.db.models.organization_request_personal_id_type import OrganizationRequestPersonalIdTypeEntity
from app.db.models.organization_receive_personal_id_type import OrganizationReceivePersonalIdTypeEntity
from sqlalchemy import ForeignKey
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base import Base
from app.models.organization import OrganizationCreate, Organization, OrganizationUpdate
from fastapi import HTTPException
import logging
from datetime import datetime, timezone
from uuid import UUID

from app import scope_utils
from app.db.db import Database
from app.db.models.organization import OrganizationEntity
from app.db.repository.organization import OrganizationRepository
from app.models.oin import Oin

logger = logging.getLogger(__name__)


class OrganizationService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create_one(self, input: OrganizationCreate) -> Organization:
        with self.db.get_db_session() as session:
            # session.add(Parent(id=1, children=[]))
            repo = session.get_repository(OrganizationRepository)
            entity: OrganizationEntity = repo.add_one(
                OrganizationEntity(
                    external_id=input.external_id,
                    name=input.name,
                    receive_personal_id_types=[
                        OrganizationReceivePersonalIdTypeEntity(personal_id_type=personal_id_type)
                        for personal_id_type in input.receive_personal_id_types
                    ],
                    request_personal_id_types=[
                        OrganizationRequestPersonalIdTypeEntity(personal_id_type=personal_id_type)
                        for personal_id_type in input.request_personal_id_types
                    ],
                )
            )
            return Organization(**entity.to_dict())

    def get_one(self, id: UUID) -> Organization | None:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            entity: OrganizationEntity | None = repo.get_one(id)
            return Organization(**entity.to_dict()) if entity else None

    def exists(self, id: Oin) -> bool:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            return repo.exists(id)

    def get_many(
        self,
        register_id: Oin | None = None,
        name: str | None = None,
        include_deleted: bool = False,
    ) -> list[Organization]:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            entities = repo.get_many(register_id=register_id, name=name, include_deleted=include_deleted)

            return [Organization(**entity.to_dict()) for entity in entities]

    def update_one(self, id: UUID, organization_update: OrganizationUpdate) -> Organization:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            organization_entity: OrganizationEntity = repo.get_one(id)
            if not organization_entity:
                logger.debug("Organization not found for update id=%s", id)
                raise HTTPException(status_code=404)
            organization_entity.external_id = organization_update.external_id
            organization_entity.name = organization_update.name
            organization_entity.updated_at = datetime.now(tz=timezone.utc)
            if organization_entity.deleted_at and not organization_update.deleted:
                organization_entity.deleted_at = None
            if not organization_entity.deleted_at and organization_update.deleted:
                organization_entity.deleted_at = datetime.now(tz=timezone.utc)
            OrganizationService.update_receive_personal_id_types(organization_entity, organization_update)
            OrganizationService.update_request_personal_id_types(organization_entity, organization_update)

            session.commit()
            return Organization(**organization_entity.to_dict())

    @staticmethod
    def update_receive_personal_id_types(
        organization_entity: OrganizationEntity, organization_update: OrganizationUpdate
    ):
        current = set([_type.personal_id_type for _type in organization_entity.receive_personal_id_types])
        updated = set(organization_update.receive_personal_id_types)

        to_add = updated - current
        to_remove = [e for e in organization_entity.receive_personal_id_types if e.personal_id_type not in updated]

        for entry in to_add:
            organization_entity.receive_personal_id_types.append(
                OrganizationReceivePersonalIdTypeEntity(personal_id_type=entry)
            )

        for entry in to_remove:
            organization_entity.receive_personal_id_types.remove(entry)

    @staticmethod
    def update_request_personal_id_types(
        organization_entity: OrganizationEntity, organization_update: OrganizationUpdate
    ):
        current = set([_type.personal_id_type for _type in organization_entity.request_personal_id_types])
        updated = set(organization_update.request_personal_id_types)

        to_add = updated - current
        to_remove = [e for e in organization_entity.request_personal_id_types if e.personal_id_type not in updated]

        for entry in to_add:
            organization_entity.request_personal_id_types.append(
                OrganizationRequestPersonalIdTypeEntity(personal_id_type=entry)
            )

        for entry in to_remove:
            organization_entity.request_personal_id_types.remove(entry)

    def delete_one(self, id: UUID) -> Organization:
        with self.db.get_db_session() as session:
            repo = session.get_repository(OrganizationRepository)
            entity = repo.get_one(id)
            if not entity:
                logger.debug("Organization not found for update id=%s", id)
                raise HTTPException(status_code=404)
            entity.updated_at = entity.deleted_at = datetime.now(tz=timezone.utc)
            ret_value = Organization(**entity.to_dict())
            session.commit()
            return ret_value

            # TODO GB: Enable this check
            # if any(client.deleted_at is None for client in organization.clients):
            #    logger.warning("Cannot delete organization with active clients organization_id=%s", id)
            #    raise OrganizationHasClientsError()
