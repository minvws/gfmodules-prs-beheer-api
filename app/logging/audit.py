import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self

import gfmodules.logging as gflog

from app.db.models.certificate import CertificateEntity
from app.logging.events import Log
from app.models.oin import Oin
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


@dataclass(frozen=True)
class AuditedClient:
    organization_identifier: str
    acting_organization_identifiers: list[str]
    common_name: list[str]
    scopes: list[str]
    deleted_at: datetime | None

    @classmethod
    def of(
        cls,
        organization_oin: Oin,
        certificates: Iterable[CertificateEntity],
        scopes: Iterable[str],
        deleted_at: datetime | None,
    ) -> Self:
        linked = list(certificates)
        return cls(
            organization_identifier=str(organization_oin),
            acting_organization_identifiers=sorted({certificate.organization_identifier for certificate in linked}),
            common_name=sorted({certificate.domain for certificate in linked}),
            scopes=scope_names(scopes),
            deleted_at=deleted_at,
        )

    def identity(self) -> dict[str, Any]:
        return {
            "organization_identifier": self.organization_identifier,
            "acting_organization_identifiers": self.acting_organization_identifiers,
        }


def client_registered(client: AuditedClient) -> None:
    gflog.emit(
        logger,
        Log.CLIENT_REGISTERED,
        "client registered",
        fields={**client.identity(), "common_name": client.common_name, "scopes": client.scopes},
    )


def client_withdrawn(client: AuditedClient) -> None:
    gflog.emit(logger, Log.CLIENT_WITHDRAWN, "client withdrawn", fields=client.identity())


def client_updated(before: AuditedClient, after: AuditedClient) -> None:
    if before.deleted_at is None and after.deleted_at is not None:
        client_withdrawn(after)
    if before.deleted_at is not None and after.deleted_at is None:
        client_registered(after)
    if before.scopes != after.scopes:
        gflog.emit(
            logger,
            Log.SCOPES_CHANGED,
            "client scopes changed",
            fields={**after.identity(), "changed_scopes": after.scopes},
        )
