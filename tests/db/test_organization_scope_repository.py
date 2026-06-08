from app.db.models.organization import OrganizationEntity
from app.db.models.scope import ScopeEntity
from app.db.repository.organization_scope import OrganizationScopeRepository


def test_add_and_has_scope(
    organization_scope_repository: OrganizationScopeRepository,
    persisted_organization: OrganizationEntity,
    persisted_scope: ScopeEntity,
) -> None:
    with organization_scope_repository.db_session:
        organization_scope_repository.add(persisted_organization.id, persisted_scope.id)
        assert organization_scope_repository.has_scope(persisted_organization.id, persisted_scope.id)


def test_has_scope_not_assigned(
    organization_scope_repository: OrganizationScopeRepository,
    persisted_organization: OrganizationEntity,
    persisted_scope: ScopeEntity,
) -> None:
    with organization_scope_repository.db_session:
        assert not organization_scope_repository.has_scope(persisted_organization.id, persisted_scope.id)


def test_remove_scope(
    organization_scope_repository: OrganizationScopeRepository,
    persisted_organization: OrganizationEntity,
    persisted_scope: ScopeEntity,
) -> None:
    with organization_scope_repository.db_session:
        organization_scope_repository.add(persisted_organization.id, persisted_scope.id)
        organization_scope_repository.remove(persisted_organization.id, persisted_scope.id)
        assert not organization_scope_repository.has_scope(persisted_organization.id, persisted_scope.id)
