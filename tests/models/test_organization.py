from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.db.models.organization import OrganizationEntity
from app.db.models.personal_id_type import PersonalIdTypeEntity
from app.enums.personal_id_type import PersonalIdType
from app.models.organization import Organization, OrganizationCreate, OrganizationUpdate
from tests.conftest import TEST_EXTERNAL_ID, TEST_ORG_NAME


def test_create_should_succeed() -> None:
    model = OrganizationCreate(
        external_id=TEST_EXTERNAL_ID,
        name=TEST_ORG_NAME,
        receive_personal_id_types=[PersonalIdType.OPRF],
        request_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
    )
    assert model.external_id == TEST_EXTERNAL_ID
    assert model.name == TEST_ORG_NAME
    assert model.receive_personal_id_types == [PersonalIdType.OPRF]
    assert model.request_personal_id_types == [PersonalIdType.REVERSIBLE_PSEUDONYM]


def test_create_missing_register_id_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(name=TEST_ORG_NAME)  # type: ignore[call-arg]


def test_create_missing_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(external_id=TEST_EXTERNAL_ID)  # type: ignore[call-arg]


def test_update_should_succeed() -> None:
    model = OrganizationUpdate(
        external_id=TEST_EXTERNAL_ID,
        name="New Name",
        receive_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
        request_personal_id_types=[PersonalIdType.OPRF],
        deleted=False,
    )
    assert model.name == "New Name"
    assert model.external_id == TEST_EXTERNAL_ID
    assert model.receive_personal_id_types == [PersonalIdType.REVERSIBLE_PSEUDONYM]
    assert model.request_personal_id_types == [PersonalIdType.OPRF]
    assert model.deleted == False


def test_update_missing_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationUpdate(  # type: ignore[call-arg]
            external_id=TEST_EXTERNAL_ID,
            receive_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF],
            deleted=False,
        )


def test_update_missing_register_id_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationUpdate(  # type: ignore[call-arg]
            name=TEST_ORG_NAME,
            receive_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF],
            deleted=False,
        )


def test_update_missing_receive_pids_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationUpdate(  # type: ignore[call-arg]
            external_id=TEST_EXTERNAL_ID,
            name=TEST_ORG_NAME,
            request_personal_id_types=[PersonalIdType.OPRF],
            deleted=False,
        )


def test_update_missing_request_pids_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationUpdate(  # type: ignore[call-arg]
            external_id=TEST_EXTERNAL_ID,
            name=TEST_ORG_NAME,
            receive_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
            deleted=False,
        )


def test_update_missing_delete_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationUpdate(  # type: ignore[call-arg]
            external_id=TEST_EXTERNAL_ID,
            name=TEST_ORG_NAME,
            receive_personal_id_types=[PersonalIdType.REVERSIBLE_PSEUDONYM],
            request_personal_id_types=[PersonalIdType.OPRF],
        )


def test_response_model_from_entity() -> None:
    entity = OrganizationEntity(
        id=uuid4(),
        external_id=TEST_EXTERNAL_ID,
        name=TEST_ORG_NAME,
        receive_personal_id_types=[PersonalIdTypeEntity(name=PersonalIdType.OPRF)],
        request_personal_id_types=[PersonalIdTypeEntity(name=PersonalIdType.OPRF)],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None,
    )
    model = Organization.model_validate(entity.to_dict())
    assert model.id == entity.id
