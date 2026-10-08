import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture

from app.db.models.client import ClientEntity
from app.db.models.organization import OrganizationEntity
from app.db.repository.client import ClientRepository
from app.db.session import DbSession
from app.enums.authorization_scope import AuthorizationScope
from app.enums.personal_id_type import PersonalIdType
from app.models.certificate import CertificateFields
from app.models.client import (
    ClientCreate,
    ClientQueryParams,
    ClientUpdate,
    ResolveRequest,
    ResolveResponse,
)
from app.models.oin import Oin
from app.models.organization import OrganizationCreate
from app.services.certificate import CertificateService
from app.services.client import ClientService
from app.services.organization import OrganizationService
from tests.conftest import TEST_EXTERNAL_ID, TEST_OIN, TEST_OIN_2, TEST_ORG_NAME

ALT_OIN = Oin("00000099000000002000")
SCOPED_ORG_REGISTER_ID = Oin("00000099000000007000")


def test_create_one_should_succeed(
    client_service: ClientService,
    persisted_organization: OrganizationEntity,
) -> None:
    result = client_service.create_one(
        persisted_organization.id,
        ClientCreate(
            scopes=[AuthorizationScope.ADMINISTRATION],
            request_personal_id_types=[PersonalIdType.OPRF],
        ),
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
        ClientUpdate(scopes=[AuthorizationScope.ADMINISTRATION], request_personal_id_types=[], deleted=False),
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
            ClientUpdate(scopes=[AuthorizationScope.ADMINISTRATION], request_personal_id_types=[], deleted=False),
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
            persisted_organization.id,
            ClientCreate(scopes=[AuthorizationScope.ADMINISTRATION], request_personal_id_types=[PersonalIdType.OPRF]),
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
        ClientCreate(scopes=[AuthorizationScope.ADMINISTRATION], request_personal_id_types=[PersonalIdType.OPRF]),
    )
    client_service.update_one(
        created.id,
        persisted_organization.id,
        ClientUpdate(scopes=[AuthorizationScope.ADMINISTRATION], deleted=True, request_personal_id_types=[]),
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
                scopes=[AuthorizationScope.ADMINISTRATION],
                request_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
                deleted=False,
            ),
        )
    assert e.value.status_code == 404
    assert e.value.detail == "The following Personal id types do not exist in the organization: reversible_pseudonym"


@pytest.mark.parametrize(
    ["organization_external_id", "certificate_domains", "certificate_organization_identifier", "resolve_response"],
    [
        (
            TEST_EXTERNAL_ID,
            ["domain.example.com"],
            TEST_OIN,
            ResolveResponse(
                scopes="prs:administration", organization_name=TEST_ORG_NAME, matched_domain="domain.example.com"
            ),
        ),
        (
            TEST_EXTERNAL_ID,
            ["other.example.com", "domain.example.com"],
            TEST_OIN,
            ResolveResponse(
                scopes="prs:administration", organization_name=TEST_ORG_NAME, matched_domain="domain.example.com"
            ),
        ),
        (
            TEST_EXTERNAL_ID,
            ["domain.example.com"],
            TEST_OIN_2,
            None,
        ),
        (
            TEST_EXTERNAL_ID,
            ["invalid.example.com"],
            TEST_OIN,
            None,
        ),
        (
            TEST_OIN_2,
            ["domain.example.com"],
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
    certificate_domains: list[str],
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
            scopes=[AuthorizationScope.ADMINISTRATION],
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
                    certificate_domains=certificate_domains,
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
                certificate_domains=certificate_domains,
                certificate_organization_identifier=str(certificate_organization_identifier),
            )
        )
        assert resolved == resolve_response


def _link_certificates(client_service: ClientService, client: ClientEntity, certificate_ids: list[UUID]) -> None:
    client_service.update_one(
        client.id,
        client.organization_id,
        ClientUpdate(
            scopes=[AuthorizationScope.ADMINISTRATION],
            request_personal_id_types=[PersonalIdType.OPRF],
            certificates=certificate_ids,
            deleted=False,
        ),
    )


def test_resolve_should_reject_deleted_certificate(
    client_service: ClientService,
    certificate_service: CertificateService,
    persisted_client_entity: ClientEntity,
) -> None:
    org_id = persisted_client_entity.organization_id
    certificate = certificate_service.create_one(
        org_id, CertificateFields(organization_identifier=str(TEST_OIN), domain="domain.example.com")
    )
    _link_certificates(client_service, persisted_client_entity, [certificate.id])
    certificate_service.delete_one(org_id, certificate.id)

    with pytest.raises(HTTPException) as e:
        client_service.resolve(
            ResolveRequest(
                client_id=persisted_client_entity.id,
                organization_external_id=TEST_EXTERNAL_ID,
                certificate_domains=["domain.example.com"],
                certificate_organization_identifier=str(TEST_OIN),
            )
        )
    assert e.value.status_code == 404
    assert e.value.detail == "Client authorization does not exist for given parameters"


def test_resolve_should_match_active_certificate_when_another_is_deleted(
    client_service: ClientService,
    certificate_service: CertificateService,
    persisted_client_entity: ClientEntity,
    mocker: MockerFixture,
) -> None:
    org_id = persisted_client_entity.organization_id
    deleted = certificate_service.create_one(
        org_id, CertificateFields(organization_identifier=str(TEST_OIN), domain="deleted.example.com")
    )
    active = certificate_service.create_one(
        org_id, CertificateFields(organization_identifier=str(TEST_OIN), domain="active.example.com")
    )
    _link_certificates(client_service, persisted_client_entity, [deleted.id, active.id])
    certificate_service.delete_one(org_id, deleted.id)

    # The certificate load order is not defined; put the deleted one first so it would be matched if not skipped
    original = ClientRepository.get_many_for_certificates

    def deleted_first(self: ClientRepository, **kwargs: Any) -> Sequence[ClientEntity]:
        entities = original(self, **kwargs)
        for entity in entities:
            entity.certificates.sort(key=lambda c: c.deleted_at is None)
        return entities

    mocker.patch.object(ClientRepository, "get_many_for_certificates", deleted_first)

    resolved = client_service.resolve(
        ResolveRequest(
            client_id=persisted_client_entity.id,
            organization_external_id=TEST_EXTERNAL_ID,
            certificate_domains=["deleted.example.com", "active.example.com"],
            certificate_organization_identifier=str(TEST_OIN),
        )
    )
    assert resolved.matched_domain == "active.example.com"


def test_resolve_should_reject_client_of_deleted_organization(
    client_service: ClientService,
    certificate_service: CertificateService,
    persisted_client_entity: ClientEntity,
    db_session: DbSession,
) -> None:
    org_id = persisted_client_entity.organization_id
    certificate = certificate_service.create_one(
        org_id, CertificateFields(organization_identifier=str(TEST_OIN), domain="domain.example.com")
    )
    _link_certificates(client_service, persisted_client_entity, [certificate.id])
    # Deleting an organization with active clients is refused by the service, but may exist from before that check
    persisted_client_entity.organization.deleted_at = datetime.now(tz=timezone.utc)
    db_session.commit()

    with pytest.raises(HTTPException) as e:
        client_service.resolve(
            ResolveRequest(
                client_id=persisted_client_entity.id,
                organization_external_id=TEST_EXTERNAL_ID,
                certificate_domains=["domain.example.com"],
                certificate_organization_identifier=str(TEST_OIN),
            )
        )
    assert e.value.status_code == 404
    assert e.value.detail == "Client authorization does not exist for given parameters"


def _unusable_certificate_id(
    kind: str,
    certificate_service: CertificateService,
    organization_service: OrganizationService,
    organization_id: UUID,
) -> UUID:
    if kind == "unknown":
        return uuid4()
    if kind == "deleted":
        deleted = certificate_service.create_one(
            organization_id, CertificateFields(organization_identifier=str(TEST_OIN), domain="deleted.example.com")
        )
        certificate_service.delete_one(organization_id, deleted.id)
        return deleted.id
    other_org = organization_service.create_one(
        OrganizationCreate(
            external_id=TEST_OIN_2,
            name="Other Organization",
            scopes=[AuthorizationScope.ADMINISTRATION],
            receive_personal_id_types=[PersonalIdType.OPRF],
            request_personal_id_types=[PersonalIdType.OPRF],
        )
    )
    return certificate_service.create_one(
        other_org.id, CertificateFields(organization_identifier=str(TEST_OIN), domain="other.example.com")
    ).id


@pytest.mark.parametrize("kind", ["unknown", "deleted", "other_organization"])
def test_create_one_should_reject_unusable_certificate(
    client_service: ClientService,
    certificate_service: CertificateService,
    organization_service: OrganizationService,
    persisted_organization: OrganizationEntity,
    kind: str,
) -> None:
    target_id = _unusable_certificate_id(kind, certificate_service, organization_service, persisted_organization.id)

    with pytest.raises(HTTPException) as e:
        client_service.create_one(
            persisted_organization.id,
            ClientCreate(
                scopes=[AuthorizationScope.ADMINISTRATION],
                request_personal_id_types=[PersonalIdType.OPRF],
                certificates=[target_id],
            ),
        )
    assert e.value.status_code == 404
    assert e.value.detail == "Not all requested certificates exists"
    assert client_service.get_many(persisted_organization.id, ClientQueryParams()) == []


@pytest.mark.parametrize("kind", ["unknown", "deleted", "other_organization"])
def test_update_one_should_reject_unusable_certificate(
    client_service: ClientService,
    certificate_service: CertificateService,
    organization_service: OrganizationService,
    persisted_client_entity: ClientEntity,
    kind: str,
) -> None:
    org_id = persisted_client_entity.organization_id
    linked = certificate_service.create_one(
        org_id, CertificateFields(organization_identifier=str(TEST_OIN), domain="linked.example.com")
    )
    _link_certificates(client_service, persisted_client_entity, [linked.id])
    target_id = _unusable_certificate_id(kind, certificate_service, organization_service, org_id)

    with pytest.raises(HTTPException) as e:
        _link_certificates(client_service, persisted_client_entity, [linked.id, target_id])
    assert e.value.status_code == 404
    assert e.value.detail == "Not all requested certificates exists"

    persisted = client_service.get_one(persisted_client_entity.id, org_id)
    assert persisted.certificates == [linked.id]


def test_create_and_update_should_accept_duplicate_certificate_ids(
    client_service: ClientService,
    certificate_service: CertificateService,
    persisted_organization: OrganizationEntity,
) -> None:
    certificate = certificate_service.create_one(
        persisted_organization.id,
        CertificateFields(organization_identifier=str(TEST_OIN), domain="domain.example.com"),
    )

    created = client_service.create_one(
        persisted_organization.id,
        ClientCreate(
            scopes=[AuthorizationScope.ADMINISTRATION],
            request_personal_id_types=[PersonalIdType.OPRF],
            certificates=[certificate.id, certificate.id],
        ),
    )
    assert created.certificates == [certificate.id]

    updated = client_service.update_one(
        created.id,
        persisted_organization.id,
        ClientUpdate(
            scopes=[AuthorizationScope.ADMINISTRATION],
            request_personal_id_types=[PersonalIdType.OPRF],
            certificates=[certificate.id, certificate.id],
            deleted=False,
        ),
    )
    assert updated.certificates == [certificate.id]
