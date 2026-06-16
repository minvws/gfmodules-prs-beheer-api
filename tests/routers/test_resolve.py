from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from tests.conftest import VALID_OIN

RESOLVE = "/clients/resolve"
ORG_OIN = "00000099000000009000"


def _body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {"oin": str(VALID_OIN), "common_name": "Client", "org_oin": ORG_OIN}
    body.update(overrides)
    return body


@pytest.mark.parametrize("scopes", ["read write", "read", ""])
def test_resolve_returns_scopes(api: TestClient, mock_client_service: MagicMock, scopes: str) -> None:
    mock_client_service.resolve.return_value = scopes

    response = api.post(RESOLVE, json=_body())

    assert response.status_code == 200
    assert response.json().get("scopes") == scopes
    call = mock_client_service.resolve.call_args
    assert str(call.kwargs["oin"]) == str(VALID_OIN)
    assert call.kwargs["common_name"] == "Client"
    assert str(call.kwargs["register_id"]) == ORG_OIN


def test_resolve_unknown_client_returns_404(api: TestClient, mock_client_service: MagicMock) -> None:
    mock_client_service.resolve.return_value = None
    response = api.post(RESOLVE, json=_body())
    assert response.status_code == 404
    assert response.json()["detail"] == "Client not found."


@pytest.mark.parametrize(
    "body",
    [
        {"common_name": "C", "org_oin": ORG_OIN},  # missing oin
        {"oin": str(VALID_OIN), "org_oin": ORG_OIN},  # missing common_name
        {"oin": str(VALID_OIN), "common_name": "C"},  # missing org_oin
        {"oin": "invalid-oin", "common_name": "C", "org_oin": ORG_OIN},  # malformed oin
    ],
)
def test_resolve_invalid_body_returns_422(
    api: TestClient, mock_client_service: MagicMock, body: dict[str, object]
) -> None:
    response = api.post(RESOLVE, json=body)
    assert response.status_code == 422
    mock_client_service.resolve.assert_not_called()
