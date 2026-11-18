from collections.abc import Iterable
from typing import TYPE_CHECKING

from gfmodules.logging import UNSET, ContextField, set_context
from gfmodules.logging.context import sanitize_free_text

from app.models.oin import Oin

if TYPE_CHECKING:
    from app.db.models.certificate import CertificateEntity

ACTOR = ContextField(name="actor_cn", header="x-gf-act-cn", sanitizer=sanitize_free_text, always_keep=True)
REPRESENTED_ORGANIZATION_IDENTIFIER = ContextField(
    name="represented_organization_identifier", header=None, always_keep=True
)
REPRESENTED_ORGANIZATION_NAME = ContextField(name="represented_organization_name", header=None)
ACTING_ORGANIZATION_IDENTIFIERS = ContextField(name="acting_organization_identifiers", header=None, always_keep=True)
CLIENT_NAME = ContextField(name="client_name", header=None)

CONTEXT_FIELDS: tuple[ContextField, ...] = (
    ACTOR,
    REPRESENTED_ORGANIZATION_IDENTIFIER,
    REPRESENTED_ORGANIZATION_NAME,
    ACTING_ORGANIZATION_IDENTIFIERS,
    CLIENT_NAME,
)
NAMES: tuple[str, ...] = (REPRESENTED_ORGANIZATION_NAME.name, CLIENT_NAME.name)


def organization_in_context(identifier: Oin, name: str) -> None:
    set_context(
        {
            REPRESENTED_ORGANIZATION_IDENTIFIER.name: str(identifier),
            REPRESENTED_ORGANIZATION_NAME.name: name,
        }
    )


def client_in_context(name: str, certificates: Iterable["CertificateEntity"]) -> None:
    identifiers = sorted(
        {certificate.organization_identifier for certificate in certificates if certificate.deleted_at is None}
    )
    set_context(
        {
            CLIENT_NAME.name: name,
            ACTING_ORGANIZATION_IDENTIFIERS.name: ",".join(identifiers) or UNSET,
        }
    )
