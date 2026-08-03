from datetime import datetime as now
from typing import Any, Generator
from uuid import uuid4

import inject
import pytest
from pydantic import ValidationError

from app.models.oin import Oin
from app.models.organization import Organization, OrganizationCreate, OrganizationUpdate
from tests.conftest import TEST_ORG_NAME, TEST_REGISTER_ID


@pytest.fixture(autouse=True)
def configure_allowed_scopes() -> Generator[Any, Any, Any]:
    inject.clear_and_configure(lambda binder: binder.bind("allowed_scopes", {"read", "write"}))
    yield
    inject.clear()


def test_create_should_succeed() -> None:
    model = OrganizationCreate(register_id=TEST_REGISTER_ID, name=TEST_ORG_NAME)
    assert model.register_id == TEST_REGISTER_ID
    assert model.name == TEST_ORG_NAME
    assert model.scopes is None


def test_create_with_scopes_should_succeed() -> None:
    model = OrganizationCreate(register_id=TEST_REGISTER_ID, name=TEST_ORG_NAME, scopes="read write")
    assert model.scopes == "read write"


def test_create_with_disallowed_scopes_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(register_id=TEST_REGISTER_ID, name=TEST_ORG_NAME, scopes="admin")


def test_create_missing_register_id_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(name=TEST_ORG_NAME)  # type: ignore[call-arg]


def test_create_missing_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(register_id=TEST_REGISTER_ID)  # type: ignore[call-arg]


def test_update_should_succeed() -> None:
    model = OrganizationUpdate(register_id=TEST_REGISTER_ID, name="New Name", scopes="read")
    assert model.name == "New Name"
    assert model.scopes == "read"


def test_update_allows_register_id() -> None:
    new_register_id = Oin("00000099000000008000")
    model = OrganizationUpdate(register_id=new_register_id, name="New Name", scopes="write")
    assert model.register_id == new_register_id
    assert model.name == "New Name"


def test_update_missing_name_is_422() -> None:
    with pytest.raises(ValidationError):
        OrganizationUpdate(register_id=TEST_REGISTER_ID)  # type: ignore[call-arg]


def test_update_missing_register_id_is_422() -> None:
    with pytest.raises(ValidationError):
        OrganizationUpdate(name="New Name")  # type: ignore[call-arg]


def test_update_without_scopes_defaults_to_none() -> None:
    model = OrganizationUpdate(register_id=TEST_REGISTER_ID, name="New Name")
    assert model.scopes is None


def test_update_requires_all_fields() -> None:
    model = OrganizationUpdate(register_id=TEST_REGISTER_ID, name="New Name", scopes="read")
    assert model.model_dump(exclude_unset=True) == {
        "register_id": TEST_REGISTER_ID,
        "name": "New Name",
        "scopes": "read",
    }


def test_response_model_from_entity_with_none_scopes() -> None:
    class _Entity:
        id = uuid4()
        register_id = TEST_REGISTER_ID
        name = TEST_ORG_NAME
        scopes = None
        created_at = now.now()
        deleted_at = None

    model = Organization.model_validate(_Entity())
    assert model.scopes is None


def test_response_model_allows_scopes_no_longer_configured() -> None:
    """Narrowing the configured allow-list must not make existing records unreadable."""

    class _Entity:
        id = uuid4()
        register_id = TEST_REGISTER_ID
        name = TEST_ORG_NAME
        scopes = "admin"
        created_at = now.now()
        deleted_at = None

    model = Organization.model_validate(_Entity())
    assert model.scopes == "admin"
