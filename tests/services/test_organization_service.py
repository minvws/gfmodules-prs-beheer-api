from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.db.db import Database
from app.db.models.client import ClientEntity
from app.db.models.organization import OrganizationEntity
from app.enums.personal_id_type import PersonalIdType
from app.models.client import ClientCreate, ClientFields, ClientUpdate
from app.models.oin import Oin
from app.models.organization import OrganizationCreate, OrganizationUpdate
from app.services.client import ClientService
from app.services.organization import OrganizationService
from tests.conftest import TEST_OIN, TEST_OIN_2, TEST_ORG_NAME

SECOND_ORG_REG_ID = Oin("00000099000000008000")
SECOND_ORG_NAME = "Second Test Organization"


def test_create_and_update_should_update_name_and_deleted(database: Database) -> None:
    service = OrganizationService(database)
    created = service.create_one(
        OrganizationCreate(
            external_id=TEST_OIN,
            receive_personal_id_types=[PersonalIdType.OPRF],
            request_personal_id_types=[PersonalIdType.OPRF],
            name=TEST_ORG_NAME,
        )
    )
    result = service.update_one(
        created.id,
        OrganizationUpdate(
            external_id=TEST_OIN_2,
            receive_personal_id_types=[PersonalIdType.OPRF],
            request_personal_id_types=[PersonalIdType.OPRF],
            name="Renamed",
            deleted=True,
        ),
    )
    assert result is not None
    assert result.name == "Renamed"
    assert result.deleted_at is not None
    assert result.external_id == TEST_OIN_2


def test_get_one_should_succeed(
    organization_service: OrganizationService,
    persisted_organization: OrganizationEntity,
) -> None:
    result = organization_service.get_one(persisted_organization.id)
    assert result is not None
    assert result.id == persisted_organization.id
    assert result.deleted_at == persisted_organization.deleted_at
    assert result.external_id == persisted_organization.external_id


def test_get_one_returns_none_when_not_found(
    organization_service: OrganizationService,
) -> None:
    with pytest.raises(HTTPException) as e:
        organization_service.get_one(uuid4())
    assert e.value.status_code == 404
    assert e.value.detail == "Organization not found"


def test_delete_one_blocked_when_client_exists(
    organization_service: OrganizationService,
    persisted_client_entity: ClientEntity,
) -> None:
    with pytest.raises(HTTPException) as e:
        organization_service.delete_one(persisted_client_entity.organization_id)

    persisted = organization_service.get_one(persisted_client_entity.organization_id)
    assert persisted is not None
    assert persisted.deleted_at is None
    assert e.value.status_code == 403
    assert e.value.detail == "Organization still has active clients"


def test_delete_one_allowed_when_clients_are_deleted(
    organization_service: OrganizationService,
    client_service: ClientService,
    persisted_client_entity: ClientEntity,
) -> None:
    client_service.delete_one(persisted_client_entity.id, persisted_client_entity.organization_id)
    organization_service.delete_one(persisted_client_entity.organization_id)
    updated = organization_service.get_one(persisted_client_entity.organization_id)
    assert updated.deleted_at is not None
    assert updated.id == persisted_client_entity.organization_id


def test_update_one_scope_can_be_removed_and_added_back(
    organization_service: OrganizationService,
) -> None:

    created = organization_service.create_one(
        OrganizationCreate(
            external_id=TEST_OIN,
            receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            name="created",
        )
    )
    assert created.receive_personal_id_types == [PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM]
    assert created.request_personal_id_types == [PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM]

    updated = organization_service.update_one(
        created.id,
        OrganizationUpdate(
            external_id=TEST_OIN,
            receive_personal_id_types=[PersonalIdType.OPRF],
            request_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
            name="updated",
            deleted=False,
        ),
    )
    assert updated is not None
    assert updated.receive_personal_id_types == [PersonalIdType.OPRF]
    assert updated.request_personal_id_types == [PersonalIdType.REVERSIBLE_PSEUDONYM]

    updated_back = organization_service.update_one(
        created.id,
        OrganizationUpdate(
            external_id=TEST_OIN,
            receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            name="updated_back",
            deleted=False,
        ),
    )
    assert updated_back is not None
    assert updated_back.receive_personal_id_types == [PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM]
    assert updated_back.request_personal_id_types == [PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM]

    persisted = organization_service.get_one(created.id)
    assert persisted is not None
    assert persisted.receive_personal_id_types == [PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM]
    assert persisted.request_personal_id_types == [PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM]


def test_update_one_scope_removal_blocked_when_used_by_client(
    organization_service: OrganizationService,
    client_service: ClientService,
) -> None:
    created = organization_service.create_one(
        OrganizationCreate(
            external_id=TEST_OIN,
            receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            name="created",
        )
    )
    assert created.receive_personal_id_types == [PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM]
    assert created.request_personal_id_types == [PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM]

    created_client = client_service.create_one(
        created.id, ClientCreate(request_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM])
    )

    with pytest.raises(IntegrityError) as e:
        organization_service.update_one(
            created.id,
            OrganizationUpdate(
                external_id=TEST_OIN,
                receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
                request_personal_id_types=[PersonalIdType.OPRF],
                name="updated",
                deleted=False,
            ),
        )
    ## The failing foreign key constraint name is not available because the tests run in SQLite
    assert str(e.value.orig) == "FOREIGN KEY constraint failed"

    persisted_client = client_service.get_one(created_client.id, created.id)
    assert persisted_client is not None
    assert persisted_client.request_personal_id_types == [PersonalIdType.REVERSIBLE_PSEUDONYM]

    persisted = organization_service.get_one(created.id)
    assert persisted is not None
    assert persisted.request_personal_id_types == [PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM]

    # test_update_one_scope_removal_allowed_when_client_no_longer_uses_it
    client_service.update_one(
        persisted_client.id, persisted.id, ClientUpdate(request_personal_id_types=[], deleted=False)
    )

    result = organization_service.update_one(
        created.id,
        OrganizationUpdate(
            external_id=TEST_OIN,
            receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF],
            name="updated",
            deleted=False,
        ),
    )
    assert result is not None
    assert result.request_personal_id_types == [PersonalIdType.OPRF]


def test_update_one_register_id_conflict_raises_integrity_error(
    organization_service: OrganizationService,
) -> None:
    first = organization_service.create_one(
        OrganizationCreate(
            external_id=TEST_OIN,
            receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            name="first",
        )
    )
    second = organization_service.create_one(
        OrganizationCreate(
            external_id=TEST_OIN_2,
            receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            name="second",
        )
    )
    with pytest.raises(IntegrityError):
        organization_service.update_one(
            first.id,
            OrganizationUpdate(
                external_id=second.external_id,
                receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
                request_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
                name="first",
                deleted=False,
            ),
        )


def test_update_one_returns_none_when_not_found(
    organization_service: OrganizationService,
) -> None:
    with pytest.raises(HTTPException) as e:
        organization_service.update_one(
            uuid4(),
            OrganizationUpdate(
                external_id=TEST_OIN,
                receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
                request_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
                name="first",
                deleted=False,
            ),
        )
    assert e.value.status_code == 404
    assert e.value.detail == "Organization not found"


def test_get_many_returns_empty_when_none(
    organization_service: OrganizationService,
) -> None:
    results = organization_service.get_many()
    assert results == []


def test_get_many_returns_all(
    organization_service: OrganizationService,
) -> None:
    first = organization_service.create_one(
        OrganizationCreate(
            external_id=TEST_OIN,
            receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            name="first",
        )
    )
    second = organization_service.create_one(
        OrganizationCreate(
            external_id=TEST_OIN_2,
            receive_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF, PersonalIdType.REVERSIBLE_PSEUDONYM],
            name="second",
        )
    )
    results = organization_service.get_many()
    assert [first.id, second.id] == [r.id for r in results]

    organization_service.update_one(
        second.id,
        OrganizationUpdate(
            external_id=TEST_OIN_2,
            receive_personal_id_types=[PersonalIdType.OPRF],
            request_personal_id_types=[PersonalIdType.OPRF],
            name="Renamed",
            deleted=True,
        ),
    )

    # test_get_many_excludes_deleted
    results_after_delete = organization_service.get_many()
    assert [first.id] == [r.id for r in results_after_delete]


def test_get_many_filters_by_register_id(
    organization_service: OrganizationService,
    persisted_organization: OrganizationEntity,
) -> None:
    results = organization_service.get_many(external_id=persisted_organization.external_id)
    assert len(results) == 1
    assert results[0].external_id == persisted_organization.external_id


def test_get_many_filters_by_name(
    organization_service: OrganizationService,
    persisted_organization: OrganizationEntity,
) -> None:
    results = organization_service.get_many(name=persisted_organization.name)
    assert len(results) == 1
    assert results[0].name == persisted_organization.name
