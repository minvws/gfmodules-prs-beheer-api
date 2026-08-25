from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.enums.personal_id_type import PersonalIdType
from app.models.organization import OrganizationCreate
from tests.conftest import FIXED_CREATED_AT, TEST_ORG_NAME, VALID_OIN, make_organization_entity

ORG_ID = UUID("11111111-1111-1111-1111-111111111111")

ORGANIZATION_BODIES = [
    {
        "name": "Org",
        "receive_personal_id_types": ["oprf"],
        "request_personal_id_types": ["reversible_pseudonym"],
    },  # missing external_id
    {
        "external_id": str(VALID_OIN),
        "receive_personal_id_types": ["oprf"],
        "request_personal_id_types": ["reversible_pseudonym"],
    },  # missing name
    {
        "external_id": str(VALID_OIN),
        "name": "Org",
        "request_personal_id_types": ["reversible_pseudonym"],
    },  # missing receive_personal_id_types
    {
        "external_id": str(VALID_OIN),
        "name": "Org",
        "receive_personal_id_types": ["oprf"],
    },  # Missing request_personal_id_types
    {
        "external_id": str(VALID_OIN),
        "name": "Org",
        "receive_personal_id_types": ["invalid"],
        "request_personal_id_types": ["reversible_pseudonym"],
    },  # Invalid receive_personal_id_types
    {
        "external_id": str(VALID_OIN),
        "name": "Org",
        "receive_personal_id_types": ["oprf"],
        "request_personal_id_types": ["invalid"],
    },  # invalid request_personal_id_types
    {},  # missing everything
]


def test_register_returns_201(api: TestClient, mock_organization_service: MagicMock) -> None:
    entity = make_organization_entity(id=ORG_ID)
    mock_organization_service.create_one.return_value = entity

    body: dict[str, object] = {
        "external_id": str(VALID_OIN),
        "name": "Org",
        "receive_personal_id_types": ["oprf"],
        "request_personal_id_types": ["reversible_pseudonym"],
    }
    response = api.post("/organizations", json=body)

    assert response.status_code == 201
    data = response.json()
    assert data == {
        "id": str(ORG_ID),
        "external_id": VALID_OIN.value,
        "name": TEST_ORG_NAME,
        "created_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "receive_personal_id_types": ["oprf"],
        "request_personal_id_types": ["reversible_pseudonym"],
    }
    mock_organization_service.create_one.assert_called_once_with(
        OrganizationCreate(
            external_id=VALID_OIN,
            name="Org",
            receive_personal_id_types=[PersonalIdType.OPRF],
            request_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
        )
    )


@pytest.mark.parametrize("body", ORGANIZATION_BODIES)
def test_register_invalid_body_returns_422(
    api: TestClient, mock_organization_service: MagicMock, body: dict[str, object]
) -> None:
    response = api.post("/organizations", json=body)
    assert response.status_code == 422
    mock_organization_service.create_one.assert_not_called()


def test_get_by_id_returns_200(api: TestClient, mock_organization_service: MagicMock) -> None:
    entity = make_organization_entity()
    mock_organization_service.get_one.return_value = entity

    response = api.get(f"/organizations/{entity.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(entity.id)
    mock_organization_service.get_one.assert_called_once_with(entity.id)


def test_get_by_id_not_found_returns_404(api: TestClient, mock_organization_service: MagicMock) -> None:
    mock_organization_service.get_one.return_value = None
    response = api.get(f"/organizations/{ORG_ID}")
    assert response.status_code == 404


def test_get_by_id_invalid_uuid_returns_422(api: TestClient) -> None:
    response = api.get("/organizations/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.parametrize("count", [0, 1, 3])
def test_get_many_returns_list(api: TestClient, mock_organization_service: MagicMock, count: int) -> None:
    mock_organization_service.get_many.return_value = [make_organization_entity(name=f"Org {i}") for i in range(count)]
    response = api.get("/organizations")
    assert response.status_code == 200
    assert len(response.json()) == count


def test_get_many_without_params_uses_defaults(api: TestClient, mock_organization_service: MagicMock) -> None:
    mock_organization_service.get_many.return_value = []
    api.get("/organizations")
    mock_organization_service.get_many.assert_called_once_with(external_id=None, name=None, include_deleted=False)


@pytest.mark.parametrize(
    "query, expected",
    [
        (
            f"external_id={VALID_OIN}",
            {"external_id": VALID_OIN, "name": None, "include_deleted": False},
        ),
        ("name=Acme", {"external_id": None, "name": "Acme", "include_deleted": False}),
        ("include_deleted=true", {"external_id": None, "name": None, "include_deleted": True}),
    ],
)
def test_get_many_passes_query_params(
    api: TestClient, mock_organization_service: MagicMock, query: str, expected: dict[str, object]
) -> None:
    mock_organization_service.get_many.return_value = []
    api.get(f"/organizations?{query}")
    mock_organization_service.get_many.assert_called_once_with(**expected)


@pytest.mark.parametrize("value", ["maybe", "2", "-1"])
def test_get_many_invalid_include_deleted_returns_422(api: TestClient, value: str) -> None:
    response = api.get(f"/organizations?include_deleted={value}")
    assert response.status_code == 422


def test_update_returns_200(api: TestClient, mock_organization_service: MagicMock) -> None:
    entity = make_organization_entity(name="New Name")
    mock_organization_service.update_one.return_value = entity
    body: dict[str, object] = {
        "external_id": str(VALID_OIN),
        "name": "Org",
        "receive_personal_id_types": ["oprf"],
        "request_personal_id_types": ["reversible_pseudonym"],
        "deleted": False,
    }
    response = api.put(
        f"/organizations/{entity.id}",
        json=body,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.parametrize("body", ORGANIZATION_BODIES)
def test_update_returns_422(api: TestClient, mock_organization_service: MagicMock, body: dict[str, object]) -> None:
    response = api.put(f"/organizations/{ORG_ID}", json={**body, "deleted": "False"})
    assert response.status_code == 422
    mock_organization_service.update_one.assert_not_called()


def test_update_invalid_uuid_returns_422(api: TestClient) -> None:
    body: dict[str, object] = {
        "external_id": str(VALID_OIN),
        "name": "Org",
        "receive_personal_id_types": ["oprf"],
        "request_personal_id_types": ["reversible_pseudonym"],
        "deleted": False,
    }
    response = api.put("/organizations/not-a-uuid", json=body)
    assert response.status_code == 422


def test_delete_returns_204(api: TestClient, mock_organization_service: MagicMock) -> None:
    mock_organization_service.delete_one.return_value = make_organization_entity(
        id=ORG_ID,
        deleted_at=FIXED_CREATED_AT,
    )
    response = api.delete(f"/organizations/{ORG_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "id": str(ORG_ID),
        "external_id": VALID_OIN.value,
        "name": TEST_ORG_NAME,
        "created_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "deleted_at": FIXED_CREATED_AT.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "receive_personal_id_types": ["oprf"],
        "request_personal_id_types": ["reversible_pseudonym"],
    }
    mock_organization_service.delete_one.assert_called_once_with(ORG_ID)


def test_delete_invalid_uuid_returns_422(api: TestClient) -> None:
    response = api.delete("/organizations/not-a-uuid")
    assert response.status_code == 422
