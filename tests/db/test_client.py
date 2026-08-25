from datetime import datetime, timezone
from uuid import uuid4

from app.db.models.client import ClientEntity
from app.db.models.organization import OrganizationEntity
from app.db.repository.client import ClientRepository
from app.db.session import DbSession


def test_add_one(client_repository: ClientRepository, client_entity: ClientEntity, db_session: DbSession) -> None:
    result = client_repository.add_one(client_entity)
    assert result == client_entity
    assert result.id is None
    db_session.commit()
    assert result.id is not None

    saved = client_repository.get_one(client_entity.organization_id, client_entity.id)
    assert saved is not None
    assert saved.id == result.id


def test_get_one_found(
    client_repository: ClientRepository,
    persisted_client_entity: ClientEntity,
) -> None:
    result = client_repository.get_one(persisted_client_entity.organization_id, persisted_client_entity.id)
    assert result is not None
    assert result.id == persisted_client_entity.id


def test_get_one_not_found(
    client_repository: ClientRepository,
    persisted_client_entity: ClientEntity,
) -> None:
    assert client_repository.get_one(uuid4(), persisted_client_entity.id) is None


def test_get_one_wrong_organization(
    client_repository: ClientRepository,
    persisted_client_entity: ClientEntity,
) -> None:
    assert client_repository.get_one(uuid4(), persisted_client_entity.id) is None


def test_exists_found(
    client_repository: ClientRepository,
    persisted_client_entity: ClientEntity,
) -> None:
    assert client_repository.exists(persisted_client_entity.organization_id, persisted_client_entity.id) is True


def test_exists_not_found(
    client_repository: ClientRepository,
    persisted_client_entity: ClientEntity,
) -> None:
    assert client_repository.exists(uuid4(), persisted_client_entity.id) is False


def test_get_many_excludes_deleted(
    client_repository: ClientRepository,
    persisted_client_entity: ClientEntity,
    db_session: DbSession,
) -> None:
    persisted_client_entity.deleted_at = datetime.now(tz=timezone.utc)
    db_session.commit()
    assert client_repository.get_many(organization_id=persisted_client_entity.organization_id) == []


def test_get_many_include_deleted_returns_deleted(
    client_repository: ClientRepository,
    persisted_client_entity: ClientEntity,
    db_session: DbSession,
) -> None:
    persisted_client_entity.deleted_at = datetime.now(tz=timezone.utc)
    db_session.commit()
    results = client_repository.get_many(organization_id=persisted_client_entity.organization_id, include_deleted=True)
    assert len(results) == 1
    assert results[0].id == persisted_client_entity.id


def test_get_many_scoped_to_organization(
    client_repository: ClientRepository,
    persisted_client_entity: ClientEntity,
) -> None:
    assert persisted_client_entity not in client_repository.get_many(organization_id=uuid4())


def test_accessing_organization(
    client_repository: ClientRepository,
    persisted_client_entity: ClientEntity,
    persisted_organization: OrganizationEntity,
) -> None:
    result = client_repository.get_one(persisted_client_entity.organization_id, persisted_client_entity.id)
    assert result is not None
    assert persisted_organization == result.organization
