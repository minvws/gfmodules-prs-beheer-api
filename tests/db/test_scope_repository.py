from uuid import uuid4

from app.db.models.scope import ScopeEntity
from app.db.repository.scope import ScopeRepository


def test_add_and_get_one(scope_repository: ScopeRepository, scope_entity: ScopeEntity) -> None:
    with scope_repository.db_session:
        scope_repository.add_one(scope_entity)
        result = scope_repository.get_one(scope_entity.id)
        assert result is not None
        assert result.id == scope_entity.id


def test_get_one_not_found(scope_repository: ScopeRepository) -> None:
    with scope_repository.db_session:
        assert scope_repository.get_one(uuid4()) is None


def test_get_by_name(scope_repository: ScopeRepository, scope_entity: ScopeEntity) -> None:
    with scope_repository.db_session:
        scope_repository.add_one(scope_entity)
        result = scope_repository.get_by_name(scope_entity.name)
        assert result is not None
        assert result.name == scope_entity.name


def test_get_many_active_only(scope_repository: ScopeRepository) -> None:
    with scope_repository.db_session:
        scope_repository.add_one(ScopeEntity(name="active:scope", active=True))
        scope_repository.add_one(ScopeEntity(name="inactive:scope", active=False))
        results = scope_repository.get_many(active_only=True)
        assert len(results) == 1
        assert results[0].name == "active:scope"
