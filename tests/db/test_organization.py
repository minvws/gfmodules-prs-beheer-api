from datetime import datetime, timezone
from uuid import uuid4

from app.db.models.organization import OrganizationEntity
from app.db.repository.organization import OrganizationRepository
from app.db.session import DbSession
from app.models.oin import Oin
from tests.conftest import TEST_EXTERNAL_ID


def test_add_one(
    organization_repository: OrganizationRepository,
    organization_entity: OrganizationEntity,
    db_session: DbSession,
) -> None:
    result = organization_repository.add_one(organization_entity)
    assert result == organization_entity
    assert result.id is None
    db_session.commit()

    saved = organization_repository.get_one(organization_entity.id)
    assert saved is not None
    assert saved.id == organization_entity.id


def test_get_one_found(
    organization_repository: OrganizationRepository,
    persisted_organization: OrganizationEntity,
) -> None:
    result = organization_repository.get_one(persisted_organization.id)
    assert result is not None
    assert result.id == persisted_organization.id


def test_get_one_not_found(
    organization_repository: OrganizationRepository,
    persisted_organization: OrganizationEntity,
) -> None:
    assert persisted_organization.id is not None
    assert organization_repository.get_one(uuid4()) is None


def test_get_many_returns_all(
    organization_repository: OrganizationRepository,
    persisted_organization: OrganizationEntity,
) -> None:
    entity_2 = OrganizationEntity(external_id=Oin("00000099000000002000"), name="Another Organization")
    organization_repository.add_one(persisted_organization)
    organization_repository.add_one(entity_2)
    assert len(organization_repository.get_many()) == 2


def test_get_many_filters_by_external_id(
    organization_repository: OrganizationRepository,
    persisted_organization: OrganizationEntity,
) -> None:
    entity_2 = OrganizationEntity(external_id=Oin("00000099000000002000"), name="Another Organization")
    organization_repository.add_one(entity_2)
    results = organization_repository.get_many(external_id=TEST_EXTERNAL_ID)
    assert len(results) == 1
    assert results[0].id == persisted_organization.id


def test_get_many_excludes_deleted(
    organization_repository: OrganizationRepository,
    persisted_organization: OrganizationEntity,
    db_session: DbSession,
) -> None:
    persisted_organization.deleted_at = datetime.now(timezone.utc)
    assert organization_repository.get_many() == []


def test_get_many_include_deleted_returns_deleted(
    organization_repository: OrganizationRepository,
    persisted_organization: OrganizationEntity,
    db_session: DbSession,
) -> None:
    persisted_organization.deleted_at = datetime.now(timezone.utc)
    db_session.commit()
    results = organization_repository.get_many(include_deleted=True)
    assert len(results) == 1
    assert results[0].id == persisted_organization.id


def test_accessing_clients_raises_lazy_load(
    organization_repository: OrganizationRepository,
    persisted_organization: OrganizationEntity,
) -> None:
    organization_repository.add_one(persisted_organization)
    result = organization_repository.get_one(persisted_organization.id)
    assert result is not None
    assert result.clients == []
