from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.enums.personal_id_type import PersonalIdType
from app.models.client import ClientCreate, ClientQueryParams, ClientUpdate
from tests.conftest import CERTIFICATE_ID, FIXED_CREATED_AT, make_client_entity

ORG_ID = "11111111-1111-1111-1111-111111111111"
CLIENT_ID = "22222222-2222-2222-2222-222222222222"
BASE = f"/organizations/{ORG_ID}/clients"

CLIENT_BODIES = [
    {},
    {
        "certificates": [str(CERTIFICATE_ID)],
    },
    {
        "request_personal_id_types": ["oprf"],
        "certificates": ["INVALID"],
    },
]


def test_register_returns_201(
    api: TestClient,
    mock_client_service: MagicMock,
) -> None:
    entity = make_client_entity(organization_id=UUID(ORG_ID))
    mock_client_service.create_one.return_value = entity

    body = {
        "request_personal_id_types": ["oprf"],
        "certificates": [str(CERTIFICATE_ID)],
    }

    response = api.post(BASE, json=body)
    assert response.status_code == 201
    data = response.json()
    assert data == {
        "id": str(entity.id),
        "organization_id": ORG_ID,
        "created_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "certificates": [str(CERTIFICATE_ID)],
        "request_personal_id_types": ["reversible_pseudonym"],
    }

    mock_client_service.create_one.assert_called_once_with(
        UUID(ORG_ID),
        ClientCreate(
            request_personal_id_types=[PersonalIdType.OPRF],
            certificates=[CERTIFICATE_ID],
        ),
    )


@pytest.mark.parametrize("body", CLIENT_BODIES)
def test_register_invalid_body_returns_422(
    api: TestClient, mock_client_service: MagicMock, body: dict[str, object]
) -> None:
    response = api.post(BASE, json=body)
    assert response.status_code == 422
    mock_client_service.create_one.assert_not_called()


def test_register_invalid_org_id_returns_422(api: TestClient, mock_client_service: MagicMock) -> None:
    body = {
        "request_personal_id_types": ["oprf"],
        "certificates": [str(CERTIFICATE_ID)],
    }
    response = api.post("/organizations/INVALID/clients", json=body)
    assert response.status_code == 422
    mock_client_service.create_one.assert_not_called()


def test_get_by_id_returns_200(api: TestClient, mock_client_service: MagicMock) -> None:
    entity = make_client_entity(organization_id=UUID(ORG_ID))
    mock_client_service.get_one.return_value = entity

    response = api.get(f"{BASE}/{entity.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(entity.id)
    mock_client_service.get_one.assert_called_once_with(entity.id, UUID(ORG_ID))


@pytest.mark.parametrize(
    "path",
    [
        f"/organizations/not-a-uuid/clients/{CLIENT_ID}",  # bad organization_id
        f"{BASE}/not-a-uuid",  # bad client id
    ],
)
def test_get_by_id_invalid_uuid_returns_422(api: TestClient, path: str) -> None:
    response = api.get(path)
    assert response.status_code == 422


@pytest.mark.parametrize("count", [0, 2])
def test_get_many_returns_list(api: TestClient, mock_client_service: MagicMock, count: int) -> None:
    mock_client_service.get_many.return_value = [make_client_entity(organization_id=UUID(ORG_ID)) for i in range(count)]
    response = api.get(BASE)
    assert response.status_code == 200
    assert len(response.json()) == count


def test_get_many_without_params_uses_defaults(api: TestClient, mock_client_service: MagicMock) -> None:
    mock_client_service.get_many.return_value = []
    api.get(BASE)
    mock_client_service.get_many.assert_called_once_with(
        organization_id=UUID(ORG_ID),
        client_query_params=ClientQueryParams(
            include_deleted=False,
        ),
    )


def test_get_many_passes_query_params(api: TestClient, mock_client_service: MagicMock) -> None:
    mock_client_service.get_many.return_value = []
    api.get(f"{BASE}?include_deleted=True")
    mock_client_service.get_many.assert_called_once_with(
        organization_id=UUID(ORG_ID),
        client_query_params=ClientQueryParams(
            include_deleted=True,
        ),
    )


@pytest.mark.parametrize("query", ["include_deleted=maybe"])
def test_get_many_invalid_query_returns_422(api: TestClient, query: str) -> None:
    response = api.get(f"{BASE}?{query}")
    assert response.status_code == 422


def test_update_returns_200(api: TestClient, mock_client_service: MagicMock) -> None:
    entity = make_client_entity(organization_id=UUID(ORG_ID))
    mock_client_service.update_one.return_value = entity
    body = {
        "request_personal_id_types": ["oprf"],
        "certificates": [],
        "deleted": False,
    }
    response = api.put(f"{BASE}/{entity.id}", json=body)
    data = response.json()
    assert data == {
        "id": str(entity.id),
        "organization_id": ORG_ID,
        "created_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "certificates": [str(CERTIFICATE_ID)],
        "request_personal_id_types": ["reversible_pseudonym"],
    }

    mock_client_service.update_one.assert_called_once_with(
        entity.id,
        UUID(ORG_ID),
        ClientUpdate(
            request_personal_id_types=[PersonalIdType.OPRF],
            certificates=[],
            deleted=False,
        ),
    )
    assert response.status_code == 200


def test_delete_returns_200(api: TestClient, mock_client_service: MagicMock) -> None:
    mock_client_service.delete_one.return_value = make_client_entity(
        id=UUID(CLIENT_ID),
        organization_id=UUID(ORG_ID),
        deleted_at=FIXED_CREATED_AT,
    )
    response = api.delete(f"{BASE}/{CLIENT_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "id": CLIENT_ID,
        "organization_id": ORG_ID,
        "created_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "deleted_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "certificates": [str(CERTIFICATE_ID)],
        "request_personal_id_types": ["reversible_pseudonym"],
    }
    mock_client_service.delete_one.assert_called_once_with(UUID(CLIENT_ID), UUID(ORG_ID))
