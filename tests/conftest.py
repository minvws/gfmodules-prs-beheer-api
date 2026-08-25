from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.application import request_validation_exception_handler
from app.config import ConfigDatabase
from app.container import get_client_service, get_organization_service
from app.db.db import Database
from app.db.models.client import ClientEntity
from app.db.models.organization import OrganizationEntity
from app.db.models.organization_personal_id_type import ClientPersonalIdTypeEntity
from app.db.models.personal_id_type import PersonalIdTypeEntity
from app.db.repository.client import ClientRepository
from app.db.repository.organization import OrganizationRepository
from app.db.repository.personal_id_type import PersonalIdTypeRepository
from app.db.session import DbSession
from app.enums.personal_id_type import PersonalIdType
from app.models.client import Client
from app.models.oin import Oin
from app.models.organization import Organization
from app.routers.client import router as client_router
from app.routers.organization import router as organization_router
from app.routers.resolve import router as resolve_router
from app.services.certificate import CertificateService
from app.services.client import ClientService
from app.services.organization import OrganizationService

TEST_OIN = Oin("00000099000000001000")
TEST_OIN_2 = Oin("00000099000000002000")
TEST_EXTERNAL_ID = Oin("00000099000000009000")
TEST_ORG_NAME = "Test Organization"
TEST_COMMON_NAME = "Test Client"
VALID_OIN = TEST_OIN
FIXED_CREATED_AT = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
DEFAULT_RECEIVE_PERSONAL_ID_TYPES = [PersonalIdType.OPRF]
DEFAULT_REQUEST_PERSONAL_ID_TYPES = [PersonalIdType.REVERSIBLE_PSEUDONYM]
CERTIFICATE_ID = uuid4()
DEFAULT_CERTIFICATES = [CERTIFICATE_ID]


@pytest.fixture()
def database() -> Generator[Database, Any, None]:
    config_database = ConfigDatabase(dsn="sqlite://", retry_backoff=[])
    db = Database(config_database=config_database)
    with db.get_db_session(commit=True) as session:
        session.session.execute(text("ATTACH DATABASE ':memory:' as admin"))
        session.session.execute(text("ATTACH DATABASE ':memory:' as prs"))
        session.session.execute(text("PRAGMA foreign_keys=ON"))
    db.generate_tables()
    with db.get_db_session(commit=True) as session:
        session.add(PersonalIdTypeEntity(name=PersonalIdType.OPRF))
        session.add(PersonalIdTypeEntity(name=PersonalIdType.REVERSIBLE_PSEUDONYM))

    yield db
    db.engine.dispose()


@pytest.fixture()
def db_session(database: Database) -> Generator[DbSession, Any, None]:
    with database.get_db_session() as session:
        yield session


@pytest.fixture()
def organization_repository(db_session: DbSession) -> OrganizationRepository:
    return OrganizationRepository(db_session=db_session)


@pytest.fixture()
def client_repository(db_session: DbSession) -> ClientRepository:
    return ClientRepository(db_session=db_session)


@pytest.fixture()
def personal_id_type_repository(db_session: DbSession) -> PersonalIdTypeRepository:
    return PersonalIdTypeRepository(db_session=db_session)


@pytest.fixture()
def organization_service(database: Database) -> OrganizationService:
    return OrganizationService(database)


@pytest.fixture()
def certificate_service(database: Database) -> CertificateService:
    return CertificateService(database)


@pytest.fixture()
def client_service(
    database: Database,
) -> ClientService:
    return ClientService(database)


@pytest.fixture()
def organization_entity() -> OrganizationEntity:
    return OrganizationEntity(external_id=TEST_EXTERNAL_ID, name=TEST_ORG_NAME)


@pytest.fixture()
def client_entity(persisted_organization: OrganizationEntity) -> ClientEntity:
    return ClientEntity(
        organization_id=persisted_organization.id,
        request_personal_id_types=[
            ClientPersonalIdTypeEntity(
                organization_id=persisted_organization.id,
                personal_id_type_id=persisted_organization.receive_personal_id_types[0].id,
            )
        ],
    )


@pytest.fixture()
def persisted_client_entity(db_session: DbSession, client_entity: ClientEntity) -> ClientEntity:
    db_session.add(client_entity)
    db_session.commit()
    return client_entity


@pytest.fixture()
def persisted_organization(
    db_session: DbSession, personal_id_type_repository: PersonalIdTypeRepository
) -> OrganizationEntity:
    personal_ids = personal_id_type_repository.get_many([PersonalIdType.OPRF])
    org = OrganizationEntity(
        external_id=TEST_EXTERNAL_ID,
        name=TEST_ORG_NAME,
        receive_personal_id_types=list(personal_ids),
        request_personal_id_types=list(personal_ids),
    )
    db_session.add(org)
    db_session.commit()
    return org


@pytest.fixture()
def mock_client_service() -> MagicMock:
    return MagicMock(spec=ClientService)


@pytest.fixture()
def mock_organization_service() -> MagicMock:
    service = MagicMock(spec=OrganizationService)
    return service


@pytest.fixture()
def api(mock_client_service: MagicMock, mock_organization_service: MagicMock) -> TestClient:
    app = FastAPI()
    app.exception_handler(RequestValidationError)(request_validation_exception_handler)
    for router in (organization_router, client_router, resolve_router):
        app.include_router(router)
    app.dependency_overrides[get_client_service] = lambda: mock_client_service
    app.dependency_overrides[get_organization_service] = lambda: mock_organization_service
    return TestClient(app)


def make_organization_entity(
    *,
    id: UUID | None = None,
    external_id: Oin = VALID_OIN,
    name: str = TEST_ORG_NAME,
    receive_personal_id_types: list[PersonalIdType] = DEFAULT_RECEIVE_PERSONAL_ID_TYPES,
    request_personal_id_types: list[PersonalIdType] = DEFAULT_REQUEST_PERSONAL_ID_TYPES,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> Organization:
    return Organization(
        id=id or uuid4(),
        external_id=external_id,
        name=name,
        receive_personal_id_types=receive_personal_id_types,
        request_personal_id_types=request_personal_id_types,
        created_at=created_at or FIXED_CREATED_AT,
        updated_at=updated_at or FIXED_CREATED_AT,
        deleted_at=deleted_at,
    )


def make_client_entity(
    *,
    id: UUID | None = None,
    organization_id: UUID | None = None,
    request_personal_id_types: list[PersonalIdType] = DEFAULT_REQUEST_PERSONAL_ID_TYPES,
    certificates: list[UUID] = DEFAULT_CERTIFICATES,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> Client:
    return Client(
        id=id or uuid4(),
        organization_id=organization_id or uuid4(),
        request_personal_id_types=request_personal_id_types,
        certificates=certificates,
        created_at=created_at or FIXED_CREATED_AT,
        updated_at=updated_at or FIXED_CREATED_AT,
        deleted_at=deleted_at,
    )
