from uuid import uuid4

from app.db.models.organization import OrganizationEntity
from app.db.repository.organization import OrganizationRepository


def test_add_one_success(
    organization_repository: OrganizationRepository,
    organization_entity: OrganizationEntity,
) -> None:
    with organization_repository.db_session:
        result = organization_repository.add_one(organization_entity)
        assert result == organization_entity


def test_get_one_found(
    organization_repository: OrganizationRepository,
    organization_entity: OrganizationEntity,
) -> None:
    with organization_repository.db_session:
        organization_repository.add_one(organization_entity)
        result = organization_repository.get_one(organization_entity.id)
        assert result is not None
        assert result.id == organization_entity.id


def test_get_one_not_found(
    organization_repository: OrganizationRepository,
) -> None:
    with organization_repository.db_session:
        result = organization_repository.get_one(uuid4())
        assert result is None


def test_update_success(
    organization_repository: OrganizationRepository,
    organization_entity: OrganizationEntity,
) -> None:
    with organization_repository.db_session:
        organization_repository.add_one(organization_entity)
        result = organization_repository.update(
            id=organization_entity.id,
            name="Updated Name",
        )
        assert result is not None
        assert result.name == "Updated Name"


def test_update_ignores_invalid_fields(
    organization_repository: OrganizationRepository,
    organization_entity: OrganizationEntity,
) -> None:
    with organization_repository.db_session:
        organization_repository.add_one(organization_entity)
        result = organization_repository.update(
            id=organization_entity.id,
            non_existing_field="value",
        )
        assert result is None


def test_update_not_found(
    organization_repository: OrganizationRepository,
) -> None:
    with organization_repository.db_session:
        result = organization_repository.update(uuid4(), name="Does not exist")
        assert result is None


def test_get_many_returns_all(
    organization_repository: OrganizationRepository,
    organization_entity: OrganizationEntity,
) -> None:
    entity_2 = OrganizationEntity(
        oin="00000099000000002000",
        name="Another Organization",
    )
    with organization_repository.db_session:
        organization_repository.add_one(organization_entity)
        organization_repository.add_one(entity_2)
        results = organization_repository.get_many()
        assert len(results) == 2


def test_get_many_filters_by_oin(
    organization_repository: OrganizationRepository,
    organization_entity: OrganizationEntity,
) -> None:
    entity_2 = OrganizationEntity(
        oin="00000099000000002000",
        name="Another Organization",
    )
    with organization_repository.db_session:
        organization_repository.add_one(organization_entity)
        organization_repository.add_one(entity_2)
        results = organization_repository.get_many(oin=organization_entity.oin)
        assert len(results) == 1
        assert results[0].id == organization_entity.id


def test_get_many_excludes_deleted(
    organization_repository: OrganizationRepository,
    organization_entity: OrganizationEntity,
) -> None:
    from datetime import datetime

    with organization_repository.db_session:
        organization_repository.add_one(organization_entity)
        organization_repository.update(id=organization_entity.id, deleted_at=datetime.now())
        results = organization_repository.get_many()
        assert len(results) == 0
