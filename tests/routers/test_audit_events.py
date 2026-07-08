"""Asserts each management operation emits the correct PRS-OB audit event (issue 1040)."""

import logging
from typing import Any, Generator
from unittest.mock import MagicMock

import inject
import pytest
from fastapi.testclient import TestClient

from app.logging.events import Log
from app.services.exceptions import ScopesNotGrantedError
from tests.conftest import TEST_REGISTER_ID, VALID_OIN, make_client_entity, make_organization_entity

ORG_ID = "11111111-1111-1111-1111-111111111111"
CLIENT_ID = "22222222-2222-2222-2222-222222222222"


@pytest.fixture(autouse=True)
def configure_allowed_scopes() -> Generator[Any, Any, Any]:
    inject.clear_and_configure(lambda binder: binder.bind("allowed_scopes", {"read", "write"}))
    yield
    inject.clear()


def _record(caplog: pytest.LogCaptureFixture, event_id: str) -> logging.LogRecord:
    matches = [r for r in caplog.records if getattr(r, "event_id", None) == event_id]
    assert matches, (
        f"no log record with event_id={event_id}; got {[getattr(r, 'event_id', None) for r in caplog.records]}"
    )
    return matches[-1]


def _no_record(caplog: pytest.LogCaptureFixture, event_id: str) -> None:
    matches = [r for r in caplog.records if getattr(r, "event_id", None) == event_id]
    assert not matches


def test_organization_register_logs_260400(
    api: TestClient, mock_organization_service: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    entity = make_organization_entity(register_id=VALID_OIN, name="Org", scopes="read write")
    mock_organization_service.create_one.return_value = entity

    with caplog.at_level(logging.DEBUG):
        response = api.post(
            "/organizations", json={"register_id": str(VALID_OIN), "name": "Org", "scopes": "read write"}
        )

    assert response.status_code == 201
    record = _record(caplog, Log.ORGANIZATION_REGISTERED.event_id)
    assert record.organisatie_oin == str(VALID_OIN)  # type: ignore[attr-defined]
    assert record.bevoegdheden == "read write"  # type: ignore[attr-defined]


def test_organization_delete_logs_260401(
    api: TestClient, mock_organization_service: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    entity = make_organization_entity(register_id=VALID_OIN)
    mock_organization_service.delete_one.return_value = entity

    with caplog.at_level(logging.DEBUG):
        response = api.delete(f"/organizations/{entity.id}")

    assert response.status_code == 204
    record = _record(caplog, Log.ORGANIZATION_WITHDRAWN.event_id)
    assert record.organisatie_oin == str(VALID_OIN)  # type: ignore[attr-defined]


def test_organization_scopes_update_logs_260404(
    api: TestClient, mock_organization_service: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    entity = make_organization_entity(register_id=VALID_OIN, scopes="read")
    mock_organization_service.update_one.return_value = entity

    with caplog.at_level(logging.DEBUG):
        response = api.put(f"/organizations/{entity.id}", json={"scopes": "read"})

    assert response.status_code == 200
    record = _record(caplog, Log.SCOPES_CHANGED.event_id)
    assert record.organisatie_oin == str(VALID_OIN)  # type: ignore[attr-defined]
    assert record.changed_scopes == "read"  # type: ignore[attr-defined]


def test_organization_name_update_does_not_log_260404(
    api: TestClient, mock_organization_service: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    entity = make_organization_entity(register_id=VALID_OIN)
    mock_organization_service.update_one.return_value = entity

    with caplog.at_level(logging.DEBUG):
        response = api.put(f"/organizations/{entity.id}", json={"name": "Renamed"})

    assert response.status_code == 200
    _no_record(caplog, Log.SCOPES_CHANGED.event_id)


def test_client_register_logs_260402(
    api: TestClient,
    mock_client_service: MagicMock,
    mock_organization_service: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    organization = make_organization_entity(register_id=TEST_REGISTER_ID)
    mock_organization_service.get_one.return_value = organization
    entity = make_client_entity(oin=VALID_OIN, common_name="Client CN", scopes="read")
    mock_client_service.create_one.return_value = entity

    with caplog.at_level(logging.DEBUG):
        response = api.post(
            f"/organizations/{ORG_ID}/clients",
            json={"oin": str(VALID_OIN), "common_name": "Client CN", "scopes": "read"},
        )

    assert response.status_code == 201
    record = _record(caplog, Log.CLIENT_REGISTERED.event_id)
    assert record.organisatie_oin == str(TEST_REGISTER_ID)  # type: ignore[attr-defined]
    assert record.handelende_oin == str(VALID_OIN)  # type: ignore[attr-defined]
    assert record.common_name == "Client CN"  # type: ignore[attr-defined]
    assert record.scopes == "read"  # type: ignore[attr-defined]


def test_client_delete_logs_260403(
    api: TestClient,
    mock_client_service: MagicMock,
    mock_organization_service: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    organization = make_organization_entity(register_id=TEST_REGISTER_ID)
    mock_organization_service.get_one.return_value = organization
    entity = make_client_entity(oin=VALID_OIN)
    mock_client_service.delete_one.return_value = entity

    with caplog.at_level(logging.DEBUG):
        response = api.delete(f"/organizations/{ORG_ID}/clients/{CLIENT_ID}")

    assert response.status_code == 204
    record = _record(caplog, Log.CLIENT_WITHDRAWN.event_id)
    assert record.handelende_oin == str(VALID_OIN)  # type: ignore[attr-defined]
    assert record.organisatie_oin == str(TEST_REGISTER_ID)  # type: ignore[attr-defined]


def test_client_scopes_update_logs_260404(
    api: TestClient,
    mock_client_service: MagicMock,
    mock_organization_service: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    organization = make_organization_entity(register_id=TEST_REGISTER_ID)
    mock_organization_service.get_one.return_value = organization
    entity = make_client_entity(oin=VALID_OIN, scopes="write")
    mock_client_service.update_one.return_value = entity

    with caplog.at_level(logging.DEBUG):
        response = api.put(f"/organizations/{ORG_ID}/clients/{CLIENT_ID}", json={"scopes": "write"})

    assert response.status_code == 200
    record = _record(caplog, Log.SCOPES_CHANGED.event_id)
    assert record.organisatie_oin == str(TEST_REGISTER_ID)  # type: ignore[attr-defined]
    assert record.handelende_oin == str(VALID_OIN)  # type: ignore[attr-defined]
    assert record.changed_scopes == "write"  # type: ignore[attr-defined]


def test_client_scopes_not_granted_logs_260405(
    api: TestClient, mock_client_service: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    mock_client_service.create_one.side_effect = ScopesNotGrantedError({"write"})

    with caplog.at_level(logging.DEBUG):
        response = api.post(
            f"/organizations/{ORG_ID}/clients",
            json={"oin": str(VALID_OIN), "common_name": "Client CN", "scopes": "write"},
        )

    assert response.status_code == 422
    record = _record(caplog, Log.ONBOARDING_VALIDATION_FAILED.event_id)
    assert "write" in record.error_reason  # type: ignore[attr-defined]


def test_invalid_registration_data_logs_260405(
    api: TestClient, mock_organization_service: MagicMock, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        response = api.post("/organizations", json={"register_id": "not-an-oin", "name": "Org"})

    assert response.status_code == 422
    record = _record(caplog, Log.ONBOARDING_VALIDATION_FAILED.event_id)
    assert record.endpoint == "/organizations"  # type: ignore[attr-defined]
    assert "register_id" in record.error_reason  # type: ignore[attr-defined]
    mock_organization_service.create_one.assert_not_called()
