from collections.abc import Sequence

from sqlalchemy import and_, select

from app.db.models.scope import ScopeEntity
from app.db.repository.base import RepositoryBase
from app.enums.authorization_scope import AuthorizationScope


class ScopeRepository(RepositoryBase):
    def get_many(
        self,
        names: list[AuthorizationScope] | list[str] | None = None,
    ) -> Sequence[ScopeEntity]:
        conditions = []
        names_as_str = [str(n) for n in names] if names else []
        if names is not None:
            conditions.append(ScopeEntity.name.in_(names_as_str))
        stmt = select(ScopeEntity)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        return self.db_session.session.execute(stmt).scalars().all()
