import pytest
from pydantic import ValidationError

from app.models.client import ClientCreate, ClientUpdate
from app.models.oin import Oin


def test_create_should_succeed() -> None:
    model = ClientCreate(oin=Oin("00000009876543210000"), common_name="Test Client")
    assert str(model.oin) == "00000009876543210000"
    assert model.common_name == "Test Client"


def test_create_missing_oin_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientCreate(common_name="Test Client")  # type: ignore[call-arg]


def test_create_missing_common_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientCreate(oin=Oin("00000009876543210000"))  # type: ignore[call-arg]


def test_update_should_succeed() -> None:
    model = ClientUpdate(common_name="New Name")
    assert model.common_name == "New Name"


def test_update_missing_common_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientUpdate()  # type: ignore[call-arg]
