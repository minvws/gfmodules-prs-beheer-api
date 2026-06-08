from app.db.models.client import ClientEntity
from app.db.models.scope import ScopeEntity
from app.db.repository.client_scope import ClientScopeRepository


def test_add_and_has_scope(
    client_scope_repository: ClientScopeRepository,
    persisted_client: ClientEntity,
    persisted_scope: ScopeEntity,
) -> None:
    with client_scope_repository.db_session:
        client_scope_repository.add(persisted_client.id, persisted_scope.id)
        assert client_scope_repository.has_scope(persisted_client.id, persisted_scope.id)


def test_has_scope_not_assigned(
    client_scope_repository: ClientScopeRepository,
    persisted_client: ClientEntity,
    persisted_scope: ScopeEntity,
) -> None:
    with client_scope_repository.db_session:
        assert not client_scope_repository.has_scope(persisted_client.id, persisted_scope.id)


def test_remove_scope(
    client_scope_repository: ClientScopeRepository,
    persisted_client: ClientEntity,
    persisted_scope: ScopeEntity,
) -> None:
    with client_scope_repository.db_session:
        client_scope_repository.add(persisted_client.id, persisted_scope.id)
        client_scope_repository.remove(persisted_client.id, persisted_scope.id)
        assert not client_scope_repository.has_scope(persisted_client.id, persisted_scope.id)
