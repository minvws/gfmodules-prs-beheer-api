from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from gfmodules.logging import LoggingStreams, access_logger_name
from gfmodules.logging.middleware import RequestContextMiddleware
from gfmodules.logging.testing import capture_stream

from app import application
from app.container import get_organization_service
from app.enums.authorization_scope import AuthorizationScope
from app.enums.personal_id_type import PersonalIdType
from app.logging import audit
from app.logging.events import ACTOR, ORGANIZATION
from app.models.organization import OrganizationCreate
from app.routers.organization import router as organization_router
from app.services.organization import OrganizationService
from tests.conftest import TEST_OIN, TEST_ORG_NAME

ADMINISTRATOR = "beheer.example.nl"


def _client(organization_service: OrganizationService | MagicMock) -> TestClient:
    fastapi = FastAPI()
    fastapi.include_router(organization_router)
    fastapi.dependency_overrides[get_organization_service] = lambda: organization_service
    fastapi.add_exception_handler(Exception, application._unhandled_exception_handler)
    fastapi.add_middleware(RequestContextMiddleware)
    return TestClient(fastapi, raise_server_exceptions=False, headers={"x-gf-act-cn": ADMINISTRATOR})


def test_audit_and_access_records_name_the_administrator_and_the_organization(
    organization_service: OrganizationService,
) -> None:
    client = _client(organization_service)
    create = OrganizationCreate(
        external_id=TEST_OIN,
        name=TEST_ORG_NAME,
        scopes=[AuthorizationScope.ADMINISTRATION],
        receive_personal_id_types=[PersonalIdType.OPRF],
        request_personal_id_types=[PersonalIdType.OPRF],
    )

    with (
        capture_stream(LoggingStreams.SIEM, audit.logger.name) as audited,
        capture_stream(LoggingStreams.APP, access_logger_name()) as accessed,
    ):
        organization_id = client.post("/organizations", json=create.model_dump(mode="json")).json()["id"]
        client.delete(f"/organizations/{organization_id}")

    expected = (ADMINISTRATOR, organization_id)
    assert [(message[ACTOR.name], message[ORGANIZATION.name]) for message in audited] == [expected, expected]
    assert [(message[ACTOR.name], message[ORGANIZATION.name]) for message in accessed] == [expected, expected]


def test_an_unhandled_exception_names_the_administrator_and_the_organization() -> None:
    failing = MagicMock()
    failing.get_one.side_effect = RuntimeError("explode")
    organization_id = str(uuid4())

    with (
        capture_stream(LoggingStreams.APP, application.logger.name) as app_stream,
        capture_stream(LoggingStreams.SIEM, application.logger.name) as siem_stream,
    ):
        response = _client(failing).get(f"/organizations/{organization_id}")

    assert response.status_code == 500
    for message in (*app_stream, *siem_stream):
        assert (message[ACTOR.name], message[ORGANIZATION.name]) == (ADMINISTRATOR, organization_id)
    assert len(app_stream) == len(siem_stream) == 1
