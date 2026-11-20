import logging
from collections.abc import Callable, Iterable

import gfmodules.logging as gflog

from app.logging.events import Log
from app.models.client import Client
from app.models.organization import Organization

logger = logging.getLogger(__name__)

Audited = Organization | Client


def _scopes(entity: Audited) -> list[str]:
    return sorted(str(scope) for scope in entity.scopes)


def _updated(before: Audited, after: Audited, registered: Callable[[], None], withdrawn: Callable[[], None]) -> None:
    if before.deleted_at is None and after.deleted_at is not None:
        withdrawn()
    if before.deleted_at is not None and after.deleted_at is None:
        registered()
    if _scopes(before) != _scopes(after):
        gflog.emit(logger, Log.SCOPES_CHANGED, "scopes changed", fields={"changed_scopes": _scopes(after)})


def organization_registered(organization: Organization) -> None:
    gflog.emit(logger, Log.ORGANIZATION_REGISTERED, "organization registered", fields={"scopes": _scopes(organization)})


def organization_withdrawn() -> None:
    gflog.emit(logger, Log.ORGANIZATION_WITHDRAWN, "organization withdrawn")


def organization_updated(before: Organization, after: Organization) -> None:
    _updated(before, after, lambda: organization_registered(after), organization_withdrawn)


def client_registered(client: Client, common_names: Iterable[str]) -> None:
    fields = {"common_name": sorted(set(common_names)), "scopes": _scopes(client)}
    gflog.emit(logger, Log.CLIENT_REGISTERED, "client registered", fields=fields)


def client_withdrawn() -> None:
    gflog.emit(logger, Log.CLIENT_WITHDRAWN, "client withdrawn")


def client_updated(before: Client, after: Client, common_names: Iterable[str]) -> None:
    _updated(before, after, lambda: client_registered(after, common_names), client_withdrawn)
