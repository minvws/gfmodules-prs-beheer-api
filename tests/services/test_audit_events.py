from collections.abc import Generator
from typing import Any

import pytest
from gfmodules.logging import LoggingStreams, bind_context
from gfmodules.logging.testing import capture_records, capture_stream

from app.db.models.organization import OrganizationEntity
from app.enums.authorization_scope import AuthorizationScope
from app.enums.personal_id_type import PersonalIdType
from app.exceptions import OrganizationHasActiveClientsError
from app.logging import context
from app.logging.events import Log
from app.models.certificate import CertificateFields
from app.models.client import ClientCreate, ClientUpdate
from app.models.organization import OrganizationCreate, OrganizationUpdate
from app.services.certificate import CertificateService
from app.services.client import ClientService
from app.services.organization import OrganizationService
from tests.conftest import TEST_COMMON_NAME, TEST_EXTERNAL_ID, TEST_OIN, TEST_OIN_2, TEST_ORG_NAME

ADMINISTRATOR = "admin.example.org"
ADMINISTRATION = str(AuthorizationScope.ADMINISTRATION)
LOGGER_NAME = "app.logging.audit"


@pytest.fixture()
def audited() -> Generator[Any, None, None]:
    with (
        bind_context({context.ACTOR.name: ADMINISTRATOR}),
        capture_stream(LoggingStreams.APP, LOGGER_NAME) as app,
        capture_stream(LoggingStreams.SIEM, LOGGER_NAME) as siem,
        capture_records(LOGGER_NAME) as records,
    ):
        yield app, siem, lambda: [e.event_id for e in records.for_stream(LoggingStreams.SIEM)]


def test_an_organization_lifecycle_is_audited(organization_service: OrganizationService, audited: Any) -> None:
    app, siem, event_ids = audited
    create = OrganizationCreate(
        external_id=TEST_OIN,
        name=TEST_ORG_NAME,
        scopes=[AuthorizationScope.ADMINISTRATION],
        receive_personal_id_types=[PersonalIdType.OPRF],
        request_personal_id_types=[PersonalIdType.OPRF],
    )
    scopes = [AuthorizationScope.ADMINISTRATION, AuthorizationScope.PSEUDONYM]
    widened = OrganizationUpdate(**{**create.model_dump(), "scopes": scopes}, deleted=False)
    created = organization_service.create_one(create)
    organization_service.update_one(created.id, widened)
    organization_service.delete_one(created.id)
    organization_service.delete_one(created.id)
    organization_service.update_one(created.id, widened)
    assert event_ids() == [
        Log.ORGANIZATION_REGISTERED.event_id,
        Log.SCOPES_CHANGED.event_id,
        Log.ORGANIZATION_WITHDRAWN.event_id,
        Log.ORGANIZATION_REGISTERED.event_id,
    ]
    assert app[0]["scopes"] == [ADMINISTRATION]
    assert "scopes" not in siem[0]
    assert app[1]["changed_scopes"] == [ADMINISTRATION, str(AuthorizationScope.PSEUDONYM)]
    assert "changed_scopes" not in siem[1]
    for message in [*app, *siem]:
        assert message[context.ACTOR.name] == ADMINISTRATOR
        assert message[context.REPRESENTED_ORGANIZATION_IDENTIFIER.name] == str(TEST_OIN)
        assert context.ACTING_ORGANIZATION_IDENTIFIERS.name not in message
    assert all(m[context.REPRESENTED_ORGANIZATION_NAME.name] == TEST_ORG_NAME for m in app)
    assert all(context.REPRESENTED_ORGANIZATION_NAME.name not in m for m in siem)


def test_a_client_lifecycle_is_audited(
    organization_service: OrganizationService,
    client_service: ClientService,
    certificate_service: CertificateService,
    persisted_organization: OrganizationEntity,
    audited: Any,
) -> None:
    app, siem, event_ids = audited
    organization_id = persisted_organization.id
    certificates = [
        certificate_service.create_one(organization_id, CertificateFields(organization_identifier=str(oin), domain=d))
        for oin, d in [(TEST_OIN_2, "b.example.com"), (TEST_OIN, "a.example.com"), (TEST_OIN, "c.example.com")]
    ]
    body: dict[str, Any] = {
        "name": TEST_COMMON_NAME,
        "scopes": [AuthorizationScope.ADMINISTRATION],
        "request_personal_id_types": [PersonalIdType.OPRF],
        "certificates": [c.id for c in certificates],
    }
    client = client_service.create_one(organization_id, ClientCreate(**body))
    client_service.update_one(client.id, organization_id, ClientUpdate(**{**body, "scopes": []}, deleted=False))
    with pytest.raises(OrganizationHasActiveClientsError):
        organization_service.delete_one(organization_id)
    client_service.delete_one(client.id, organization_id)
    client_service.delete_one(client.id, organization_id)
    assert event_ids() == [Log.CLIENT_REGISTERED.event_id, Log.SCOPES_CHANGED.event_id, Log.CLIENT_WITHDRAWN.event_id]
    assert app[0]["common_name"] == ["a.example.com", "b.example.com", "c.example.com"]
    assert siem[0]["scopes"] == [ADMINISTRATION]
    assert "common_name" not in siem[0]
    assert app[1]["changed_scopes"] == []
    for message in [*app, *siem]:
        assert message[context.ACTING_ORGANIZATION_IDENTIFIERS.name] == f"{TEST_OIN},{TEST_OIN_2}"
        assert message[context.REPRESENTED_ORGANIZATION_IDENTIFIER.name] == str(TEST_EXTERNAL_ID)
    assert all(m[context.CLIENT_NAME.name] == TEST_COMMON_NAME for m in app)
    assert all(context.CLIENT_NAME.name not in m for m in siem)
