from sqlalchemy import Sequence
from uuid import UUID
from sqlalchemy.sql import select, and_
from app.db.decorator import repository
from app.db.models import CertificateEntity
from app.db.repository.base import RepositoryBase


@repository(CertificateEntity)
class CertificateRepository(RepositoryBase):
    def create_one(self, entity: CertificateEntity) -> CertificateEntity:
        self.db_session.add(entity)
        return entity

    def get_one(self, organization_id: UUID, certificate_id: UUID) -> CertificateEntity | None:
        stmt = select(CertificateEntity).where(
            and_(
                CertificateEntity.id == certificate_id,
                CertificateEntity.organization_id == organization_id,
            )
        )
        return self.db_session.execute(stmt).scalar()

    def get_many(self, organization_id: UUID) -> Sequence[CertificateEntity]:
        stmt = select(CertificateEntity).where(
            and_(
                CertificateEntity.organization_id == organization_id,
            )
        )
        return self.db_session.execute(stmt).scalars()
