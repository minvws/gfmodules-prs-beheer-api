from uuid import UUID, uuid4

from app.db.models.organization import OrganizationEntity
from app.services.client import ClientService


def test_create_one_should_succeed(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    result = client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Test Client",
    )
    assert isinstance(result.id, UUID)
    assert result.organization_id == persisted_organization.id
    assert result.oin == "00000009876543210000"
    assert result.common_name == "Test Client"


def test_get_one_should_succeed(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    created = client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Test Client",
    )
    result = client_service.get_one(created.id, persisted_organization.id)
    assert result is not None
    assert result.id == created.id


def test_get_one_returns_none_when_not_found(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    result = client_service.get_one(uuid4(), persisted_organization.id)
    assert result is None


def test_get_one_wrong_organization_returns_none(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    created = client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Test Client",
    )
    result = client_service.get_one(created.id, uuid4())
    assert result is None


def test_delete_one_soft_deletes(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    created = client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Test Client",
    )
    client_service.delete_one(created.id, persisted_organization.id)
    result = client_service.get_one(created.id, persisted_organization.id)
    assert result is None


def test_delete_one_returns_none_when_not_found(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    result = client_service.delete_one(uuid4(), persisted_organization.id)
    assert result is None


def test_update_one_should_succeed(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    created = client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Test Client",
    )
    result = client_service.update_one(created.id, persisted_organization.id, common_name="Updated Client")
    assert result is not None
    assert result.common_name == "Updated Client"
    assert result.id == created.id


def test_update_one_returns_none_when_not_found(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    result = client_service.update_one(uuid4(), persisted_organization.id, common_name="Ghost")
    assert result is None


def test_get_many_returns_empty_when_none(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    results = client_service.get_many(organization_id=persisted_organization.id)
    assert results == []


def test_get_many_returns_all(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Client A",
    )
    client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210001",
        common_name="Client B",
    )
    results = client_service.get_many(organization_id=persisted_organization.id)
    assert len(results) == 2


def test_get_many_scoped_to_organization(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Test Client",
    )
    results = client_service.get_many(organization_id=uuid4())
    assert results == []


def test_get_many_excludes_deleted(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    created = client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Test Client",
    )
    client_service.delete_one(created.id, persisted_organization.id)
    results = client_service.get_many(organization_id=persisted_organization.id)
    assert results == []


def test_get_many_filters_by_oin(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Client A",
    )
    client_service.create_one(
        organization_id=persisted_organization.id,
        oin="00000009876543210001",
        common_name="Client B",
    )
    results = client_service.get_many(organization_id=persisted_organization.id, oin="00000009876543210000")
    assert len(results) == 1
    assert results[0].oin == "00000009876543210000"
