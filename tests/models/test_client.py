from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.client import Client, ClientCreate, ClientQueryParams, ClientResolveRequest, ClientUpdate
from app.models.oin import Oin
from tests.conftest import TEST_OIN


def test_create_should_succeed() -> None:
    model = ClientCreate(oin=TEST_OIN, common_name="Test Client")
    assert model.oin == TEST_OIN
    assert model.common_name == "Test Client"
    assert model.scopes is None


def test_create_with_scopes_should_succeed() -> None:
    model = ClientCreate(oin=TEST_OIN, common_name="Test Client", scopes="read")
    assert model.scopes == "read"


def test_response_model_from_entity() -> None:
    class _Entity:
        id = uuid4()
        organization_id = uuid4()
        oin = TEST_OIN
        common_name = "Test Client"
        scopes = None
        created_at = datetime.now()
        deleted_at = None

    model = Client.model_validate(_Entity())
    assert model.id == _Entity.id


def test_create_missing_oin_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientCreate(common_name="Test Client")  # type: ignore[call-arg]


def test_create_missing_common_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientCreate(oin=TEST_OIN)  # type: ignore[call-arg]


def test_update_is_partial_all_fields_optional() -> None:
    model = ClientUpdate()
    assert model.oin is None
    assert model.common_name is None
    assert model.scopes is None


def test_update_only_tracks_supplied_fields() -> None:
    model = ClientUpdate(common_name="New Name")
    assert model.model_dump(exclude_unset=True) == {"common_name": "New Name"}


def test_update_can_set_oin_and_scopes() -> None:
    model = ClientUpdate(oin=TEST_OIN, scopes="read")
    assert model.oin == TEST_OIN
    assert model.scopes == "read"


def test_query_params_all_optional_and_track_supplied_only() -> None:
    assert ClientQueryParams().model_dump(exclude_unset=True) == {}
    params = ClientQueryParams(common_name="CN-1", scopes="read")
    assert params.model_dump(exclude_unset=True) == {"common_name": "CN-1", "scopes": "read"}


def test_resolve_request_should_succeed() -> None:
    model = ClientResolveRequest(
        oin=TEST_OIN,
        common_name="Test Client",
        org_id=Oin("00000099000000001000"),
    )
    assert model.oin == TEST_OIN
    assert model.org_id == Oin("00000099000000001000")


def test_resolve_request_missing_org_id_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientResolveRequest(  # type: ignore[call-arg]
            oin=TEST_OIN,
            common_name="Test Client",
        )
