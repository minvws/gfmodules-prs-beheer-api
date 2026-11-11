import uuid
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.db.models.certificate import CertificateEntity
from app.db.models.client import ClientEntity
from app.db.models.client_personal_id_type import ClientPersonalIdTypeEntity
from app.db.models.personal_id_type import PersonalIdTypeEntity
from app.enums.authorization_scope import AuthorizationScope
from app.enums.personal_id_type import PersonalIdType
from app.models.client import (
    CLIENT_NAME_MAX_LENGTH,
    Client,
    ClientCreate,
    ClientQueryParams,
    ClientUpdate,
    ResolveRequest,
)
from app.models.oin import Oin
from tests.conftest import TEST_OIN


def test_create_should_succeed() -> None:
    certificate_uuid = uuid.uuid4()
    model = ClientCreate(
        name="Test Client",
        scopes=[AuthorizationScope.ADMINISTRATION],
        request_personal_id_types=[PersonalIdType.OPRF],
        certificates=[certificate_uuid],
    )
    assert model.request_personal_id_types == [PersonalIdType.OPRF]
    assert model.certificates == [certificate_uuid]


def test_update_should_succeed() -> None:
    certificate_uuid = uuid.uuid4()
    model = ClientUpdate(
        name="Test Client",
        scopes=[AuthorizationScope.ADMINISTRATION],
        request_personal_id_types=[PersonalIdType.OPRF],
        certificates=[certificate_uuid],
        deleted=False,
    )
    assert model.request_personal_id_types == [PersonalIdType.OPRF]
    assert model.certificates == [certificate_uuid]
    assert model.deleted == False


def test_query_params() -> None:
    model = ClientQueryParams(include_deleted=False)
    assert model.include_deleted == False


def test_response_model_from_entity() -> None:
    entity = ClientEntity(
        name="Test Client",
        id=uuid4(),
        organization_id=uuid4(),
        certificates=[CertificateEntity(id=uuid4())],
        request_personal_id_types=[
            ClientPersonalIdTypeEntity(personal_id_type=PersonalIdTypeEntity(name=PersonalIdType.OPRF))
        ],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=None,
    )
    model = Client.model_validate(entity.to_dict())
    assert model.id == entity.id


def test_response_model_from_entity_deleted() -> None:
    entity = ClientEntity(
        name="Test Client",
        id=uuid4(),
        organization_id=uuid4(),
        certificates=[CertificateEntity(id=uuid4())],
        request_personal_id_types=[
            ClientPersonalIdTypeEntity(personal_id_type=PersonalIdTypeEntity(name=PersonalIdType.OPRF))
        ],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        deleted_at=datetime.now(timezone.utc),
    )
    model = Client.model_validate(entity.to_dict())
    assert model.id == entity.id


def test_create_missing_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientCreate()  # type: ignore[call-arg]


def test_resolve_request_should_succeed() -> None:
    client_id = uuid.uuid4()
    model = ResolveRequest(
        client_id=client_id,
        organization_external_id=TEST_OIN,
        certificate_domains=["domain"],
        certificate_organization_identifier="cert_org_id",
    )
    assert model.client_id == client_id
    assert model.organization_external_id == TEST_OIN
    assert model.certificate_domains == ["domain"]
    assert model.certificate_organization_identifier == "cert_org_id"


@pytest.mark.parametrize(
    [
        "client_id",
        "organization_external_id",
        "certificate_domains",
        "certificate_organization_identifier",
    ],
    [
        (uuid.uuid4(), None, ["domain"], "cert_org_id"),
        (None, TEST_OIN, ["domain"], "cert_org_id"),
    ],
)
def test_resolve_request_missing_fields_should_raise(
    client_id: UUID,
    organization_external_id: Oin,
    certificate_domains: list[str],
    certificate_organization_identifier: str,
) -> None:
    with pytest.raises(ValidationError) as e:
        ResolveRequest(
            client_id=client_id,
            organization_external_id=organization_external_id,
            certificate_domains=certificate_domains,
            certificate_organization_identifier=certificate_organization_identifier,
        )
    assert e.value.error_count() == 1


def _client_create(name: object) -> ClientCreate:
    return ClientCreate.model_validate(
        {
            "name": name,
            "scopes": [AuthorizationScope.ADMINISTRATION],
            "request_personal_id_types": [PersonalIdType.OPRF],
        }
    )


def test_create_name_is_stripped() -> None:
    assert _client_create("  My Client  ").name == "My Client"


def test_create_name_max_length_is_accepted() -> None:
    assert _client_create("x" * CLIENT_NAME_MAX_LENGTH).name == "x" * CLIENT_NAME_MAX_LENGTH


@pytest.mark.parametrize("name", ["", "   ", "x" * (CLIENT_NAME_MAX_LENGTH + 1), None])
def test_create_invalid_name_should_raise(name: object) -> None:
    with pytest.raises(ValidationError) as e:
        _client_create(name)
    assert e.value.errors()[0]["loc"] == ("name",)


def test_create_missing_name_should_raise() -> None:
    with pytest.raises(ValidationError) as e:
        ClientCreate(scopes=[AuthorizationScope.ADMINISTRATION], request_personal_id_types=[])  # type: ignore[call-arg]
    assert e.value.errors()[0]["loc"] == ("name",)


def test_update_missing_name_should_raise() -> None:
    with pytest.raises(ValidationError) as e:
        ClientUpdate(scopes=[], request_personal_id_types=[], deleted=False)  # type: ignore[call-arg]
    assert e.value.errors()[0]["loc"] == ("name",)


def test_response_model_includes_name() -> None:
    entity = ClientEntity(
        name="Named Client",
        id=uuid4(),
        organization_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    assert Client.model_validate(entity.to_dict()).name == "Named Client"
