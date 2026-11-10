from typing import Any

from gfmodules.logging.testing import capture_records

from app.db.models.organization import OrganizationEntity
from app.enums.authorization_scope import AuthorizationScope
from app.enums.personal_id_type import PersonalIdType
from app.logging.events import Log
from app.models.certificate import CertificateFields
from app.models.client import ClientCreate, ClientUpdate
from app.models.organization import OrganizationCreate, OrganizationUpdate
from app.services.certificate import CertificateService
from app.services.client import ClientService
from app.services.organization import OrganizationService
from tests.conftest import TEST_EXTERNAL_ID, TEST_OIN, TEST_ORG_NAME

ADMINISTRATION = str(AuthorizationScope.ADMINISTRATION)
PSEUDONYM = str(AuthorizationScope.PSEUDONYM)


def _audited(captured: Any) -> list[Any]:
    return [entry.record for entry in captured.entries]


def test_an_organization_lifecycle_is_audited(organization_service: OrganizationService) -> None:
    create = OrganizationCreate(
        external_id=TEST_OIN,
        name=TEST_ORG_NAME,
        scopes=[AuthorizationScope.ADMINISTRATION],
        receive_personal_id_types=[PersonalIdType.OPRF],
        request_personal_id_types=[PersonalIdType.OPRF],
    )
    widened = OrganizationUpdate(
        **{**create.model_dump(), "scopes": [AuthorizationScope.ADMINISTRATION, AuthorizationScope.PSEUDONYM]},
        deleted=False,
    )

    with capture_records("app.logging.audit") as captured:
        created = organization_service.create_one(create)
        organization_service.update_one(created.id, widened)
        organization_service.delete_one(created.id)
        organization_service.delete_one(created.id)
        organization_service.update_one(created.id, widened)

    registered, scopes_changed, withdrawn, restored = _audited(captured)
    assert [registered.event_id, scopes_changed.event_id, withdrawn.event_id, restored.event_id] == [
        Log.ORGANIZATION_REGISTERED.event_id,
        Log.SCOPES_CHANGED.event_id,
        Log.ORGANIZATION_WITHDRAWN.event_id,
        Log.ORGANIZATION_REGISTERED.event_id,
    ]
    assert registered.organization_identifier == str(TEST_OIN)
    assert registered.scopes == [ADMINISTRATION]
    assert scopes_changed.changed_scopes == [ADMINISTRATION, PSEUDONYM]
    assert withdrawn.organization_identifier == str(TEST_OIN)


def test_a_client_lifecycle_is_audited(
    client_service: ClientService,
    certificate_service: CertificateService,
    persisted_organization: OrganizationEntity,
) -> None:
    certificate = certificate_service.create_one(
        persisted_organization.id,
        CertificateFields(organization_identifier=str(TEST_OIN), domain="client.example.com"),
    )

    with capture_records("app.logging.audit") as captured:
        client = client_service.create_one(
            persisted_organization.id,
            ClientCreate(
                scopes=[AuthorizationScope.ADMINISTRATION],
                request_personal_id_types=[PersonalIdType.OPRF],
                certificates=[certificate.id],
            ),
        )
        client_service.update_one(
            client.id,
            persisted_organization.id,
            ClientUpdate(
                scopes=[],
                request_personal_id_types=[PersonalIdType.OPRF],
                certificates=[certificate.id],
                deleted=False,
            ),
        )
        client_service.delete_one(client.id, persisted_organization.id)
        client_service.delete_one(client.id, persisted_organization.id)

    registered, scopes_changed, withdrawn = _audited(captured)
    assert [registered.event_id, scopes_changed.event_id, withdrawn.event_id] == [
        Log.CLIENT_REGISTERED.event_id,
        Log.SCOPES_CHANGED.event_id,
        Log.CLIENT_WITHDRAWN.event_id,
    ]
    for record in (registered, scopes_changed, withdrawn):
        assert record.organization_identifier == str(TEST_EXTERNAL_ID)
        assert record.acting_organization_identifiers == [str(TEST_OIN)]
    assert registered.common_name == ["client.example.com"]
    assert registered.scopes == [ADMINISTRATION]
    assert scopes_changed.changed_scopes == []
