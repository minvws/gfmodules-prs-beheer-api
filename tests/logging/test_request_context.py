from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from gfmodules.logging import LoggingStreams, access_logger_name
from gfmodules.logging.middleware import RequestContextMiddleware
from gfmodules.logging.testing import capture_stream

from app import application
from app.container import get_client_service, get_organization_service
from app.enums.authorization_scope import AuthorizationScope
from app.enums.personal_id_type import PersonalIdType
from app.logging.context import (
    ACTOR,
    CONTEXT_FIELDS,
    REPRESENTED_ORGANIZATION_IDENTIFIER,
    REPRESENTED_ORGANIZATION_NAME,
    set_organization_log_context,
)
from app.models.certificate import CertificateFields
from app.routers.client import router as client_router
from app.routers.organization import router as organization_router
from app.services.certificate import CertificateService
from app.services.client import ClientService
from app.services.organization import OrganizationService
from tests.conftest import TEST_COMMON_NAME, TEST_OIN, TEST_ORG_NAME

ADMINISTRATOR = "admin.example.org"
CERTIFICATE_OIN = "00000099000000003000"
RENAMED = "Renamed Organization"
FIELDS = (*(field.name for field in CONTEXT_FIELDS), "status_code")


def _client(overrides: dict[Callable[..., Any], Callable[[], Any]]) -> TestClient:
    fastapi = FastAPI()
    for router in (organization_router, client_router):
        fastapi.include_router(router)
    fastapi.add_exception_handler(Exception, application._unhandled_exception_handler)
    fastapi.add_middleware(RequestContextMiddleware)
    fastapi.dependency_overrides.update(overrides)
    return TestClient(fastapi, raise_server_exceptions=False, headers={"x-gf-act-cn": ADMINISTRATOR})


def test_a_request_logs_the_actor_and_only_the_entities_it_works_on(
    organization_service: OrganizationService,
    client_service: ClientService,
    certificate_service: CertificateService,
) -> None:
    api = _client(
        {
            get_organization_service: lambda: organization_service,
            get_client_service: lambda: client_service,
        }
    )
    organization_body = {
        "external_id": str(TEST_OIN),
        "name": TEST_ORG_NAME,
        "scopes": [AuthorizationScope.ADMINISTRATION],
        "receive_personal_id_types": [PersonalIdType.OPRF],
        "request_personal_id_types": [PersonalIdType.OPRF],
    }
    client_body = {
        "name": TEST_COMMON_NAME,
        "scopes": [AuthorizationScope.ADMINISTRATION],
        "request_personal_id_types": [PersonalIdType.OPRF],
        "certificates": [],
    }

    with capture_stream(LoggingStreams.APP, access_logger_name()) as accessed:
        organization = api.post("/organizations", json=organization_body).json()
        organization_url = f"/organizations/{organization['id']}"
        client = api.post(f"{organization_url}/clients", json=client_body).json()
        certificate = certificate_service.create_one(
            UUID(organization["id"]), CertificateFields(organization_identifier=CERTIFICATE_OIN, domain="a.example.org")
        )
        client_url = f"{organization_url}/clients/{client['id']}"
        api.put(client_url, json={**client_body, "certificates": [str(certificate.id)], "deleted": False})
        api.put(organization_url, json={**organization_body, "name": RENAMED, "deleted": False})
        api.delete(client_url)
        api.delete(organization_url)

    assert [tuple(message.get(field) for field in FIELDS) for message in accessed] == [
        (ADMINISTRATOR, str(TEST_OIN), TEST_ORG_NAME, None, None, 201),
        (ADMINISTRATOR, str(TEST_OIN), TEST_ORG_NAME, None, TEST_COMMON_NAME, 201),
        (ADMINISTRATOR, str(TEST_OIN), TEST_ORG_NAME, CERTIFICATE_OIN, TEST_COMMON_NAME, 200),
        (ADMINISTRATOR, str(TEST_OIN), RENAMED, None, None, 200),
        (ADMINISTRATOR, str(TEST_OIN), RENAMED, CERTIFICATE_OIN, TEST_COMMON_NAME, 200),
        (ADMINISTRATOR, str(TEST_OIN), RENAMED, None, None, 200),
    ]


def test_names_stay_off_siem() -> None:
    service = MagicMock(spec=OrganizationService)

    def fail(_: Any) -> None:
        set_organization_log_context(TEST_OIN, TEST_ORG_NAME)
        raise RuntimeError

    service.get_one.side_effect = fail
    api = _client({get_organization_service: lambda: service})

    with (
        capture_stream(LoggingStreams.APP, application.logger.name) as app,
        capture_stream(LoggingStreams.SIEM, application.logger.name) as siem,
    ):
        response = api.get(f"/organizations/{uuid4()}")

    assert response.status_code == 500
    assert siem[0][ACTOR.name] == ADMINISTRATOR
    assert siem[0][REPRESENTED_ORGANIZATION_IDENTIFIER.name] == str(TEST_OIN)
    assert REPRESENTED_ORGANIZATION_NAME.name not in siem[0]
    assert app[0][REPRESENTED_ORGANIZATION_NAME.name] == TEST_ORG_NAME
