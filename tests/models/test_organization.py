import pytest
from pydantic import ValidationError

from app.models.oin import Oin
from app.models.organization import OrganizationCreate, OrganizationUpdate


def test_create_should_succeed() -> None:
    model = OrganizationCreate(oin=Oin("00000099000000001000"), name="Test Organization")
    assert str(model.oin) == "00000099000000001000"
    assert model.name == "Test Organization"
    assert model.authorizations is None


def test_create_with_authorizations_should_succeed() -> None:
    model = OrganizationCreate(
        oin=Oin("00000099000000001000"),
        name="Test Organization",
        authorizations="scope:a scope:b",
    )
    assert model.authorizations == "scope:a scope:b"


def test_create_missing_oin_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(name="Test Organization")  # type: ignore[call-arg]


def test_create_missing_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(oin=Oin("00000099000000001000"))  # type: ignore[call-arg]


def test_update_should_succeed() -> None:
    model = OrganizationUpdate(name="New Name")
    assert model.name == "New Name"
    assert model.authorizations is None


def test_update_with_authorizations_should_succeed() -> None:
    model = OrganizationUpdate(name="New Name", authorizations="scope:write")
    assert model.authorizations == "scope:write"


def test_update_missing_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationUpdate()  # type: ignore[call-arg]


def test_update_model_dump_exclude_unset_omits_unset_fields() -> None:
    dumped = OrganizationUpdate(name="New Name").model_dump(exclude_unset=True)
    assert dumped == {"name": "New Name"}
    assert "authorizations" not in dumped


def test_update_model_dump_exclude_unset_includes_explicitly_set_none() -> None:
    dumped = OrganizationUpdate(name="New Name", authorizations=None).model_dump(exclude_unset=True)
    assert "authorizations" in dumped
    assert dumped["authorizations"] is None
