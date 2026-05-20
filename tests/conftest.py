from typing import Any, Generator

import pytest

from app.config import ConfigDatabase
from app.db.db import Database
from app.db.models.organization import OrganizationEntity
from app.db.repository.organization import OrganizationRepository
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
