from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import ColumnElement, and_, select

from app.db.models.client import ClientEntity
from app.db.repository.base import RepositoryBase


class ClientRepository(RepositoryBase):
    def add_one(self, data: ClientEntity) -> ClientEntity:
        self.db_session.add(data)
        return data

    def get_one(self, organization_id: UUID, id: UUID) -> ClientEntity | None:
        stmt = select(ClientEntity).where(self._and_clause(organization_id, id))
        return self.db_session.session.execute(stmt).scalar_one_or_none()

    def exists(self, organization_id: UUID, id: UUID) -> bool:
        stmt = select(select(ClientEntity.id).where(self._and_clause(organization_id, id)).exists())
        return bool(self.db_session.session.execute(stmt).scalar())

    def get_many(
        self,
        organization_id: UUID | None = None,
        client_id: UUID | None = None,
        certificate_domain: str | None = None,
        certificate_organization_identifier: str | None = None,
        include_deleted: bool = False,
    ) -> Sequence[ClientEntity]:
        conditions = []
        if organization_id is not None:
            conditions.append(ClientEntity.organization_id == organization_id)
        if client_id is not None:
            conditions.append(ClientEntity.id == client_id)
        if certificate_domain is not None:
            conditions.append(ClientEntity.certificates.any(domain=certificate_domain))
        if certificate_organization_identifier is not None:
            conditions.append(
                ClientEntity.certificates.any(organization_identifier=certificate_organization_identifier)
            )
        if not include_deleted:
            conditions.append(ClientEntity.deleted_at.is_(None))
        stmt = select(ClientEntity).where(and_(*conditions))
        return self.db_session.session.execute(stmt).scalars().all()

    def _and_clause(self, organization_id: UUID, id: UUID) -> ColumnElement[bool]:
        return and_(
            ClientEntity.organization_id == organization_id,
            ClientEntity.id == id,
            ClientEntity.deleted_at.is_(None),
        )
