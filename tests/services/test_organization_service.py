from uuid import UUID, uuid4

from app.db.models.organization import OrganizationEntity
from app.services.organization import OrganizationService


def test_create_one_should_succeed(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    result = organization_service.create_one(
        oin=organization_entity.oin,
        common_name=organization_entity.common_name,
    )
    assert isinstance(result.id, UUID)
    assert result.oin == organization_entity.oin
    assert result.common_name == organization_entity.common_name
    assert result.client_certificate is None


def test_create_one_with_certificate_should_succeed(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    cert = "-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----"
    result = organization_service.create_one(
        oin=organization_entity.oin,
        common_name=organization_entity.common_name,
        client_certificate=cert,
    )
    assert result.client_certificate == cert


def test_get_one_should_succeed(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    created = organization_service.create_one(
        oin=organization_entity.oin,
        common_name=organization_entity.common_name,
    )
    result = organization_service.get_one(created.id)
    assert result is not None
    assert result.id == created.id
    assert result.oin == created.oin


def test_get_one_returns_none_when_not_found(
    organization_service: OrganizationService,
) -> None:
    result = organization_service.get_one(uuid4())
    assert result is None


def test_delete_one_soft_deletes(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    created = organization_service.create_one(
        oin=organization_entity.oin,
        common_name=organization_entity.common_name,
    )
    organization_service.delete_one(created.id)
    result = organization_service.get_one(created.id)
    assert result is None


def test_delete_one_returns_none_when_not_found(
    organization_service: OrganizationService,
) -> None:
    result = organization_service.delete_one(uuid4())
    assert result is None


def test_update_one_should_succeed(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    created = organization_service.create_one(
        oin=organization_entity.oin,
        common_name=organization_entity.common_name,
    )
    result = organization_service.update_one(created.id, common_name="New Name")
    assert result is not None
    assert result.common_name == "New Name"
    assert result.id == created.id


def test_update_one_can_set_certificate(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    cert = "-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----"
    created = organization_service.create_one(
        oin=organization_entity.oin,
        common_name=organization_entity.common_name,
    )
    result = organization_service.update_one(created.id, common_name=created.common_name, client_certificate=cert)
    assert result is not None
    assert result.client_certificate == cert


def test_update_one_returns_none_when_not_found(
    organization_service: OrganizationService,
) -> None:
    result = organization_service.update_one(uuid4(), common_name="Ghost")
    assert result is None


def test_get_many_returns_empty_when_none(
    organization_service: OrganizationService,
) -> None:
    results = organization_service.get_many()
    assert results == []


def test_get_many_returns_all(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    organization_service.create_one(oin=organization_entity.oin, common_name=organization_entity.common_name)
    organization_service.create_one(oin="00000001234567890001", common_name="Other Org")
    results = organization_service.get_many()
    assert len(results) == 2


def test_get_many_excludes_deleted(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    created = organization_service.create_one(
        oin=organization_entity.oin,
        common_name=organization_entity.common_name,
    )
    organization_service.delete_one(created.id)
    results = organization_service.get_many()
    assert results == []


def test_get_many_filters_by_oin(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    organization_service.create_one(oin=organization_entity.oin, common_name=organization_entity.common_name)
    organization_service.create_one(oin="00000001234567890001", common_name="Other Org")

    results = organization_service.get_many(oin=organization_entity.oin)
    assert len(results) == 1
    assert results[0].oin == organization_entity.oin
