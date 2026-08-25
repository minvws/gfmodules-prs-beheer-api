import uuid
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.db.models.client import ClientEntity
from app.db.models.organization import OrganizationEntity
from app.enums.personal_id_type import PersonalIdType
from app.models.certificate import CertificateFields
from app.models.client import (
    ClientCreate,
    ClientFields,
    ClientQueryParams,
    ClientUpdate,
    ResolveRequest,
    ResolveResponse,
)
from app.models.oin import Oin
from app.services.certificate import CertificateService
from app.services.client import ClientService
from tests.conftest import TEST_EXTERNAL_ID, TEST_OIN, TEST_OIN_2, TEST_ORG_NAME

ALT_OIN = Oin("00000099000000002000")
SCOPED_ORG_REGISTER_ID = Oin("00000099000000007000")


def test_create_one_should_succeed(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    result = client_service.create_one(
        persisted_organization.id,
        ClientCreate(request_personal_id_types=[PersonalIdType.OPRF]),
    )
    assert isinstance(result.id, UUID)
    assert result.organization_id == persisted_organization.id


@pytest.mark.parametrize(
    "real_client, real_org, expected_found",
    [
        (True, True, True),
        (False, True, False),
        (True, False, False),
    ],
)
def test_get_one_lookup(
    client_service: ClientService,
    persisted_client_entity: ClientEntity,
    real_client: bool,
    real_org: bool,
    expected_found: bool,
) -> None:
    client_id = persisted_client_entity.id if real_client else uuid4()
    organization_id = persisted_client_entity.organization_id if real_org else uuid4()
    if expected_found:
        result = client_service.get_one(client_id, organization_id)
        assert result.id == persisted_client_entity.id
    else:
        with pytest.raises(HTTPException) as e:
            client_service.get_one(client_id, organization_id)
        assert e.value.status_code == 404


def test_update_one(
    client_service: ClientService,
    persisted_client_entity: ClientEntity,
) -> None:
    result = client_service.update_one(
        persisted_client_entity.id,
        persisted_client_entity.organization_id,
        ClientUpdate(request_personal_id_types=[], deleted=False),
    )
    assert result is not None
    assert result.id == persisted_client_entity.id
    assert result.request_personal_id_types == []


@pytest.mark.parametrize(["client_exists", "organization_exists"], [(True, False), (False, True)])
def test_update_one_when_not_exists(
    client_service: ClientService,
    persisted_client_entity: ClientEntity,
    client_exists: bool,
    organization_exists: bool,
) -> None:
    client_id = persisted_client_entity.id if client_exists else uuid.uuid4()
    organization_id = persisted_client_entity.organization_id if organization_exists else uuid.uuid4()
    with pytest.raises(HTTPException) as e:
        client_service.update_one(
            client_id,
            organization_id,
            ClientUpdate(request_personal_id_types=[], deleted=False),
        )
    assert e.value.status_code == 404
    assert e.value.detail == ("Organization not found" if client_exists else "Client not found")


@pytest.mark.parametrize("count", [0, 1, 2])
def test_get_many_returns_active_clients(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
    count: int,
) -> None:
    for _ in range(count):
        client_service.create_one(
            persisted_organization.id, ClientCreate(request_personal_id_types=[PersonalIdType.OPRF])
        )
    assert len(client_service.get_many(persisted_organization.id, ClientQueryParams())) == count


def test_get_many_scoped_to_organization(
    client_service: ClientService,
    persisted_client_entity: ClientEntity,
) -> None:
    assert persisted_client_entity.deleted_at is None
    assert client_service.get_many(uuid4(), ClientQueryParams()) == []


@pytest.mark.parametrize("include_deleted, expected_count", [(False, 0), (True, 1)])
def test_get_many_deleted_visibility(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
    include_deleted: bool,
    expected_count: int,
) -> None:
    created = client_service.create_one(
        persisted_organization.id,
        ClientCreate(request_personal_id_types=[PersonalIdType.OPRF]),
    )
    client_service.update_one(
        created.id,
        persisted_organization.id,
        ClientUpdate(deleted=True, request_personal_id_types=[]),
    )
    results = client_service.get_many(
        persisted_organization.id,
        ClientQueryParams(include_deleted=include_deleted),
    )
    assert len(results) == expected_count
    if include_deleted:
        assert results[0].deleted_at is not None
        assert results[0].updated_at == results[0].deleted_at


def test_update_one_scope_enforcement(
    client_service: ClientService,
    persisted_client_entity: ClientEntity,
) -> None:
    with pytest.raises(HTTPException) as e:
        client_service.update_one(
            persisted_client_entity.id,
            persisted_client_entity.organization_id,
            ClientUpdate(
                request_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
                deleted=False,
            ),
        )
    assert e.value.status_code == 404
    assert e.value.detail == "The following Personal id types do not exist in the organization: reversible_pseudonym"


@pytest.mark.parametrize(
    ["organization_external_id", "certificate_domain", "certificate_organization_identifier", "resolve_response"],
    [
        (
            TEST_EXTERNAL_ID,
            "domain.example.com",
            TEST_OIN,
            ResolveResponse(scopes="prs:oprf", organization_name=TEST_ORG_NAME),
        ),
        (
            TEST_EXTERNAL_ID,
            "domain.example.com",
            TEST_OIN_2,
            None,
        ),
        (
            TEST_EXTERNAL_ID,
            "invalid.example.com",
            TEST_OIN,
            None,
        ),
        (
            TEST_OIN_2,
            "domain.example.com",
            TEST_OIN,
            None,
        ),
    ],
)
def test_resolve(
    client_service: ClientService,
    certificate_service: CertificateService,
    persisted_client_entity: ClientEntity,
    organization_external_id: Oin,
    certificate_domain: str,
    certificate_organization_identifier: Oin,
    resolve_response: ResolveResponse | None,
) -> None:
    certificate = certificate_service.create_one(
        persisted_client_entity.organization_id,
        CertificateFields(
            organization_identifier=str(TEST_OIN),
            domain="domain.example.com",
        ),
    )
    client_service.update_one(
        persisted_client_entity.id,
        persisted_client_entity.organization_id,
        ClientUpdate(
            request_personal_id_types=[PersonalIdType.OPRF],
            certificates=[certificate.id],
            deleted=False,
        ),
    )
    if not resolve_response:
        with pytest.raises(HTTPException) as e:
            client_service.resolve(
                ResolveRequest(
                    client_id=persisted_client_entity.id,
                    organization_external_id=organization_external_id,
                    certificate_domain=certificate_domain,
                    certificate_organization_identifier=str(certificate_organization_identifier),
                )
            )
        assert e.value.status_code == 404
        assert e.value.detail == "Client authorization does not exist for given parameters"
    else:
        resolved = client_service.resolve(
            ResolveRequest(
                client_id=persisted_client_entity.id,
                organization_external_id=organization_external_id,
                certificate_domain=certificate_domain,
                certificate_organization_identifier=str(certificate_organization_identifier),
            )
        )
        assert resolved == resolve_response
