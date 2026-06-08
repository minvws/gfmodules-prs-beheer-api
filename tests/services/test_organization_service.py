from uuid import UUID, uuid4

from app.db.models.organization import OrganizationEntity
from app.models.oin import Oin
from app.services.organization import OrganizationService


def test_create_one_should_succeed(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    result = organization_service.create_one(
        oin=Oin(organization_entity.oin),  # type: ignore[attr-defined]
        common_name=organization_entity.common_name,  # type: ignore[attr-defined]
    )
    assert isinstance(result.id, UUID)
    assert result.oin == organization_entity.oin  # type: ignore[attr-defined]
    assert result.common_name == organization_entity.common_name  # type: ignore[attr-defined]
    assert result.client_certificate is None  # type: ignore[attr-defined]


def test_get_one_should_succeed(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    created = organization_service.create_one(
        oin=Oin(organization_entity.oin),  # type: ignore[attr-defined]
        common_name=organization_entity.common_name,  # type: ignore[attr-defined]
    )
    result = organization_service.get_one(created.id)
    assert result is not None
    assert result.id == created.id
    assert result.oin == created.oin  # type: ignore[attr-defined]


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
        oin=Oin(organization_entity.oin),  # type: ignore[attr-defined]
        common_name=organization_entity.common_name,  # type: ignore[attr-defined]
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
        oin=Oin(organization_entity.oin),  # type: ignore[attr-defined]
        common_name=organization_entity.common_name,  # type: ignore[attr-defined]
    )
    result = organization_service.update_one(created.id, common_name="New Name")
    assert result is not None
    assert result.common_name == "New Name"  # type: ignore[attr-defined]
    assert result.id == created.id


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
    organization_service.create_one(
        oin=Oin(organization_entity.oin),  # type: ignore[attr-defined]
        common_name=organization_entity.common_name,  # type: ignore[attr-defined]
    )
    organization_service.create_one(oin=Oin("00000099000000002000"), common_name="Other Org")
    results = organization_service.get_many()
    assert len(results) == 2


def test_get_many_excludes_deleted(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    created = organization_service.create_one(
        oin=Oin(organization_entity.oin),  # type: ignore[attr-defined]
        common_name=organization_entity.common_name,  # type: ignore[attr-defined]
    )
    organization_service.delete_one(created.id)
    results = organization_service.get_many()
    assert results == []


def test_get_many_filters_by_oin(
    organization_service: OrganizationService,
    organization_entity: OrganizationEntity,
) -> None:
    organization_service.create_one(
        oin=Oin(organization_entity.oin),  # type: ignore[attr-defined]
        common_name=organization_entity.common_name,  # type: ignore[attr-defined]
    )
    organization_service.create_one(oin=Oin("00000099000000002000"), common_name="Other Org")

    results = organization_service.get_many(oin=Oin(organization_entity.oin))  # type: ignore[attr-defined]
    assert len(results) == 1
    assert results[0].oin == organization_entity.oin  # type: ignore[attr-defined]
