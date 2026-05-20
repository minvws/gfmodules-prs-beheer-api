from typing import Any, Generator

import pytest

from app.config import ConfigDatabase
from app.db.db import Database
from app.db.models.client import ClientEntity
from app.db.models.organization import OrganizationEntity
from app.db.repository.client import ClientRepository
from app.db.repository.organization import OrganizationRepository
from app.services.client import ClientService
from app.services.organization import OrganizationService


@pytest.fixture()
def database() -> Generator[Database, Any, None]:
    config_database = ConfigDatabase(dsn="sqlite:///:memory:", retry_backoff=[])
    try:
        db = Database(config_database=config_database)
        db.generate_tables()
        yield db
    except Exception as e:
        raise e


@pytest.fixture()
def organization_repository(database: Database) -> OrganizationRepository:
    return OrganizationRepository(db_session=database.get_db_session())


@pytest.fixture()
def organization_service(database: Database) -> OrganizationService:
    return OrganizationService(database)


@pytest.fixture()
def organization_entity() -> OrganizationEntity:
    return OrganizationEntity(
        oin="00000001234567890000",
        common_name="Test Organization",
        client_certificate=None,
    )


@pytest.fixture()
def persisted_organization(organization_service: OrganizationService) -> OrganizationEntity:
    return organization_service.create_one(oin="00000001234567890000", common_name="Test Organization")


@pytest.fixture()
def client_repository(database: Database) -> ClientRepository:
    return ClientRepository(db_session=database.get_db_session())


@pytest.fixture()
def client_service(database: Database) -> ClientService:
    return ClientService(database)


@pytest.fixture()
def client_entity(persisted_organization: OrganizationEntity) -> ClientEntity:
    return ClientEntity(
        organization_id=persisted_organization.id,
        oin="00000009876543210000",
        common_name="Test Client",
    )
