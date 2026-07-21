from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from tests.conftest import VALID_OIN, make_client_entity, make_organization_entity

RESOLVE = "/clients/resolve"
ORG_OIN = "00000099000000009000"


def _body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "client_organization_id": str(VALID_OIN),
        "client_common_name": "Client",
        "organization_id": ORG_OIN,
    }
    body.update(overrides)
    return body


@pytest.mark.parametrize("scopes", ["read write", "read", ""])
def test_resolve_returns_scopes_and_organization_name(
    api: TestClient, mock_client_service: MagicMock, scopes: str
) -> None:
    org_entity = make_organization_entity(name="Test Organization")
    mock_client_service.resolve.return_value = make_client_entity(scopes=scopes, org_entity=org_entity)

    response = api.post(RESOLVE, json=_body())

    assert response.status_code == 200
    assert response.json() == {"scopes": scopes, "organization_name": "Test Organization"}
    call = mock_client_service.resolve.call_args
    assert str(call.kwargs["oin"]) == str(VALID_OIN)
    assert call.kwargs["common_name"] == "Client"
    assert str(call.kwargs["register_id"]) == ORG_OIN


def test_resolve_unknown_client_returns_404(api: TestClient, mock_client_service: MagicMock) -> None:
    mock_client_service.resolve.return_value = None
    response = api.post(RESOLVE, json=_body())
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found."


def test_resolve_client_without_scopes_returns_404(api: TestClient, mock_client_service: MagicMock) -> None:
    mock_client_service.resolve.return_value = make_client_entity(scopes=None)
    response = api.post(RESOLVE, json=_body())
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found."


@pytest.mark.parametrize(
    "body",
    [
        {"client_common_name": "C", "organization_id": ORG_OIN},  # missing client_organization_id
        {"client_organization_id": str(VALID_OIN), "organization_id": ORG_OIN},  # missing client_common_name
        {"client_organization_id": str(VALID_OIN), "client_common_name": "C"},  # missing organization_id
        {
            "client_organization_id": "invalid-oin",
            "client_common_name": "C",
            "organization_id": ORG_OIN,
        },  # malformed client_organization_id
    ],
)
def test_resolve_invalid_body_returns_422(
    api: TestClient, mock_client_service: MagicMock, body: dict[str, object]
) -> None:
    response = api.post(RESOLVE, json=body)
    assert response.status_code == 422
    mock_client_service.resolve.assert_not_called()
