import uuid
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
        "client_id": str(uuid.uuid4()),
        "certificate_organization_identifier": VALID_OIN.value,
        "certificate_domain": "Client",
        "organization_external_id": ORG_OIN,
    }
    body.update(overrides)
    return body


@pytest.mark.parametrize("scopes", ["read write", "read", ""])
def test_resolve_returns_scopes_and_organization_name(
    api: TestClient, mock_client_service: MagicMock, scopes: str
) -> None:
    resolve_response = ResolveResponse(scopes=scopes, organization_name=TEST_ORG_NAME)
    mock_client_service.resolve.return_value = resolve_response
    client_id = uuid.uuid4()

    response = api.post(RESOLVE, json=_body(client_id=str(client_id)))

    assert response.status_code == 200
    assert response.json() == {"scopes": scopes, "organization_name": "Test Organization"}
    mock_client_service.resolve.assert_called_once_with(
        ResolveRequest(
            client_id=client_id,
            organization_external_id=Oin(ORG_OIN),
            certificate_domain="Client",
            certificate_organization_identifier=VALID_OIN.value,
        )
    )


@pytest.mark.parametrize(
    "body",
    [
        {  # missing client_id
            "certificate_organization_identifier": str(VALID_OIN),
            "certificate_domain": "C",
            "organization_external_id": ORG_OIN,
        },
        {  # missing certificate_organization_identifier
            "client_id": str(uuid.uuid4()),
            "certificate_domain": "C",
            "organization_external_id": ORG_OIN,
        },
        {  # missing certificate_domain
            "client_id": str(uuid.uuid4()),
            "certificate_organization_identifier": str(VALID_OIN),
            "organization_external_id": ORG_OIN,
        },
        {  # missing organization_external_id
            "client_id": str(uuid.uuid4()),
            "certificate_organization_identifier": str(VALID_OIN),
            "certificate_domain": "C",
        },
        {  # malformed organization_external_id
            "client_id": str(uuid.uuid4()),
            "certificate_organization_identifier": str(VALID_OIN),
            "certificate_domain": "C",
            "organization_external_id": "invalid-oin",
        },
        {  # malformed client_id
            "client_id": "not-a-uuid",
            "certificate_organization_identifier": str(VALID_OIN),
            "certificate_domain": "C",
            "organization_external_id": ORG_OIN,
        },
    ],
)
def test_resolve_invalid_body_returns_422(
    api: TestClient, mock_client_service: MagicMock, body: dict[str, object]
) -> None:
    response = api.post(RESOLVE, json=body)
    assert response.status_code == 422
    mock_client_service.resolve.assert_not_called()
