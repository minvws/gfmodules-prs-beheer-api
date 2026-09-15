from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.models.client import ResolveRequest, ResolveResponse
from app.models.oin import Oin
from tests.conftest import TEST_ORG_NAME, VALID_OIN

RESOLVE = "/clients/resolve"
ORG_OIN = "00000099000000009000"


def _body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "client_organization_id": VALID_OIN.value,
        "client_common_name": "Client",
        "organization_id": ORG_OIN,
    }
    body.update(overrides)
    return body


@pytest.mark.parametrize("scopes", ["read write", "read", ""])
def test_resolve_returns_scopes_and_organization_name(
    api: TestClient, mock_client_service: MagicMock, scopes: str
) -> None:
    resolve_response = ResolveResponse(scopes=scopes, organization_name=TEST_ORG_NAME)
    mock_client_service.resolve.return_value = resolve_response

    response = api.post(RESOLVE, json=_body())

    assert response.status_code == 200
    assert response.json() == {"scopes": scopes, "organization_name": "Test Organization"}
    mock_client_service.resolve.assert_called_once_with(
        ResolveRequest(
            client_id=None,
            organization_external_id=Oin(ORG_OIN),
            certificate_domain="Client",
            certificate_organization_identifier=VALID_OIN.value,
        )
    )


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
