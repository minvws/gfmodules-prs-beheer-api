from typing import Any, Generator

import pytest

from app.config import ConfigDatabase
from app.db.db import Database
from app.db.models.client import ClientEntity
from app.db.models.organization import OrganizationEntity
from app.db.repository.client import ClientRepository
from app.db.repository.organization import OrganizationRepository

TEST_OIN = "00000099000000001000"
TEST_REGISTER_ID = "test-register-001"
TEST_ORG_NAME = "Test Organization"
TEST_MANDATE_ID = "mandate-001"
TEST_COMMON_NAME = "Test Client"


@pytest.fixture()
def database() -> Generator[Database, Any, None]:
    config_database = ConfigDatabase(dsn="sqlite:///:memory:", retry_backoff=[])
    db = Database(config_database=config_database)
    db.generate_tables()
    yield db
    db.engine.dispose()


@pytest.fixture()
def organization_repository(database: Database) -> OrganizationRepository:
    return OrganizationRepository(db_session=database.get_db_session())


@pytest.fixture()
def client_repository(database: Database) -> ClientRepository:
    return ClientRepository(db_session=database.get_db_session())


@pytest.fixture()
def organization_entity() -> OrganizationEntity:
    return OrganizationEntity(register_id=TEST_REGISTER_ID, name=TEST_ORG_NAME)


@pytest.fixture()
def persisted_organization(organization_repository: OrganizationRepository) -> OrganizationEntity:
    entity = OrganizationEntity(register_id=TEST_REGISTER_ID, name=TEST_ORG_NAME)
    with organization_repository.db_session:
        return organization_repository.add_one(entity)


@pytest.fixture()
def client_entity(persisted_organization: OrganizationEntity) -> ClientEntity:
    return ClientEntity(
        organization_id=persisted_organization.id,
        mandate_id=TEST_MANDATE_ID,
        oin=TEST_OIN,
        common_name=TEST_COMMON_NAME,
    )


@pytest.fixture()
def persisted_client(
    client_repository: ClientRepository,
    persisted_organization: OrganizationEntity,
) -> ClientEntity:
    entity = ClientEntity(
        organization_id=persisted_organization.id,
        mandate_id=TEST_MANDATE_ID,
        oin=TEST_OIN,
        common_name=TEST_COMMON_NAME,
    )
    with client_repository.db_session:
        return client_repository.add_one(entity)
