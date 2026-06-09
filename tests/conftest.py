from typing import Any, Generator

import pytest

from app.config import ConfigDatabase
from app.db.db import Database
from app.db.models.client import ClientEntity
from app.db.models.organization import OrganizationEntity
from app.db.repository.client import ClientRepository
from app.db.repository.organization import OrganizationRepository
from app.models.oin import Oin
from app.services.client import ClientService
from app.services.organization import OrganizationService


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
def organization_service(database: Database) -> OrganizationService:
    return OrganizationService(database)


@pytest.fixture()
def organization_entity() -> OrganizationEntity:
    entity = OrganizationEntity(
        register_id="00000099000000001000",
        name="Test Organization",
    )
    entity.oin = entity.register_id  # type: ignore
    entity.common_name = entity.name  # type: ignore
    entity.client_certificate = None  # type: ignore
    return entity


@pytest.fixture()
def persisted_organization(organization_service: OrganizationService) -> OrganizationEntity:
    return organization_service.create_one(oin=Oin("00000099000000001000"), common_name="Test Organization")


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
        mandate_id="00000099000000001000",
        oin="00000099000000001000",
        common_name="Test Client",
    )
