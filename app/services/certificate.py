from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException

from app.db.db import Database
from app.db.models import CertificateEntity
from app.db.repository.certificate import CertificateRepository
from app.models.certificate import Certificate, CertificateFields, CertificateQueryParams


class CertificateService:
    db: Database

    def __init__(self, db: Database):
        self.db = db

    def create_one(self, organization_id: UUID, certificate_create: CertificateFields) -> Certificate:
        with self.db.get_db_session(commit=True) as session:
            certificate_repository: CertificateRepository = session.get_repository(CertificateRepository)
            now = datetime.now(tz=timezone.utc)
            entity = certificate_repository.create_one(
                CertificateEntity(
                    organization_identifier=certificate_create.organization_identifier,
                    domain=certificate_create.domain,
                    organization_id=organization_id,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.session.flush()
            return Certificate(**entity.to_dict())

    def get_many(self, organization_id: UUID, query_params: CertificateQueryParams) -> list[Certificate]:
        with self.db.get_db_session() as session:
            certificate_repository: CertificateRepository = session.get_repository(CertificateRepository)
            entities = list(
                certificate_repository.get_many(organization_id, include_deleted=query_params.include_deleted)
            )
            return [Certificate(**entity.to_dict()) for entity in entities]

    def get_one(self, organization_id: UUID, certificate_id: UUID) -> Certificate:
        with self.db.get_db_session() as session:
            certificate_repository: CertificateRepository = session.get_repository(CertificateRepository)
            entity = certificate_repository.get_one(organization_id, certificate_id)
            if not entity:
                raise HTTPException(status_code=404, detail="Certificate not found")
            return Certificate(**entity.to_dict())

    def update_one(self, organization_id: UUID, certificate_id: UUID, update: CertificateFields) -> Certificate:
        with self.db.get_db_session(commit=True) as session:
            certificate_repository: CertificateRepository = session.get_repository(CertificateRepository)
            entity = certificate_repository.get_one(organization_id, certificate_id)
            if not entity:
                raise HTTPException(status_code=404, detail="Certificate not found")
            entity.organization_identifier = update.organization_identifier
            entity.domain = update.domain
            entity.updated_at = datetime.now(tz=timezone.utc)
            return Certificate(**entity.to_dict())

    def delete_one(self, organization_id: UUID, certificate_id: UUID) -> Certificate:
        with self.db.get_db_session(commit=True) as session:
            certificate_repository: CertificateRepository = session.get_repository(CertificateRepository)
            entity = certificate_repository.get_one(organization_id, certificate_id)
            if not entity:
                raise HTTPException(status_code=404, detail="Certificate not found")
            now = datetime.now(tz=timezone.utc)
            entity.updated_at = now
            entity.deleted_at = now
            return Certificate(**entity.to_dict())
