from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.sql import and_, select

from app.db.models import CertificateEntity
from app.db.repository.base import RepositoryBase


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

    def get_many(
        self, organization_id: UUID, certificate_ids: list[UUID] | None = None, include_deleted: bool = False
    ) -> Sequence[CertificateEntity]:
        clauses = [CertificateEntity.organization_id == organization_id]
        if certificate_ids is not None:
            clauses.append(CertificateEntity.id.in_(certificate_ids))
        if not include_deleted:
            clauses.append(CertificateEntity.deleted_at.is_(None))
        stmt = select(CertificateEntity).where(and_(*clauses))
        return self.db_session.execute(stmt).scalars().all()
