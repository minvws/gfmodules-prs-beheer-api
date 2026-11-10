import logging
from collections.abc import Iterable

import gfmodules.logging as gflog

from app.logging.events import Log
from app.models.organization import Organization

logger = logging.getLogger(__name__)


def scope_names(scopes: Iterable[str]) -> list[str]:
    return sorted(str(scope) for scope in scopes)


def organization_registered(organization: Organization) -> None:
    gflog.emit(
        logger,
        Log.ORGANIZATION_REGISTERED,
        "organization registered",
        fields={"organization_identifier": str(organization.external_id), "scopes": scope_names(organization.scopes)},
    )


def organization_withdrawn(organization: Organization) -> None:
    gflog.emit(
        logger,
        Log.ORGANIZATION_WITHDRAWN,
        "organization withdrawn",
        fields={"organization_identifier": str(organization.external_id)},
    )


def organization_updated(before: Organization, after: Organization) -> None:
    if before.deleted_at is None and after.deleted_at is not None:
        organization_withdrawn(after)
    if before.deleted_at is not None and after.deleted_at is None:
        organization_registered(after)
    if scope_names(before.scopes) != scope_names(after.scopes):
        gflog.emit(
            logger,
            Log.SCOPES_CHANGED,
            "organization scopes changed",
            fields={"organization_identifier": str(after.external_id), "changed_scopes": scope_names(after.scopes)},
        )
