from datetime import datetime
from uuid import uuid4

from app.db.models.client import ClientEntity
from app.db.repository.client import ClientRepository


def test_add_one_success(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    with client_repository.db_session:
        result = client_repository.add_one(client_entity)
        assert result == client_entity


def test_get_one_found(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    with client_repository.db_session:
        client_repository.add_one(client_entity)
        result = client_repository.get_one(client_entity.id, client_entity.organization_id)
        assert result is not None
        assert result.id == client_entity.id


def test_get_one_not_found(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    with client_repository.db_session:
        result = client_repository.get_one(uuid4(), client_entity.organization_id)
        assert result is None


def test_get_one_wrong_organization(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    with client_repository.db_session:
        client_repository.add_one(client_entity)
        result = client_repository.get_one(client_entity.id, uuid4())
        assert result is None


def test_update_success(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    with client_repository.db_session:
        client_repository.add_one(client_entity)
        result = client_repository.update(
            id=client_entity.id,
            organization_id=client_entity.organization_id,
            common_name="Updated Name",
        )
        assert result is not None
        assert result.common_name == "Updated Name"


def test_update_not_found(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    with client_repository.db_session:
        result = client_repository.update(uuid4(), client_entity.organization_id, common_name="Ghost")
        assert result is None


def test_get_many_returns_all(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    entity_2 = ClientEntity(
        organization_id=client_entity.organization_id,
        oin="00000009876543210001",
        common_name="Another Client",
    )
    with client_repository.db_session:
        client_repository.add_one(client_entity)
        client_repository.add_one(entity_2)
        results = client_repository.get_many(organization_id=client_entity.organization_id)
        assert len(results) == 2


def test_get_many_filters_by_oin(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    entity_2 = ClientEntity(
        organization_id=client_entity.organization_id,
        oin="00000009876543210001",
        common_name="Another Client",
    )
    with client_repository.db_session:
        client_repository.add_one(client_entity)
        client_repository.add_one(entity_2)
        results = client_repository.get_many(
            organization_id=client_entity.organization_id,
            oin=client_entity.oin,
        )
        assert len(results) == 1
        assert results[0].id == client_entity.id


def test_get_many_excludes_deleted(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    with client_repository.db_session:
        client_repository.add_one(client_entity)
        client_repository.update(
            id=client_entity.id,
            organization_id=client_entity.organization_id,
            deleted_at=datetime.now(),
        )
        results = client_repository.get_many(organization_id=client_entity.organization_id)
        assert len(results) == 0


def test_get_many_scoped_to_organization(
    client_repository: ClientRepository,
    client_entity: ClientEntity,
) -> None:
    with client_repository.db_session:
        client_repository.add_one(client_entity)
        results = client_repository.get_many(organization_id=uuid4())
        assert len(results) == 0
