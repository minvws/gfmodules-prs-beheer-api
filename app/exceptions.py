"""
Domain exceptions raised by the service layer.
"""

from collections.abc import Sequence


class DomainError(Exception):
    """Base class for errors the service layer reports to its callers."""

    message: str = "Request could not be processed"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class OrganizationNotFoundError(DomainError):
    message = "Organization not found"


class OrganizationHasActiveClientsError(DomainError):
    """The organization cannot be deleted while it has clients that are not deleted."""

    message = "Organization still has active clients"


class ClientNotFoundError(DomainError):
    message = "Client not found"


class ClientAuthorizationNotFoundError(DomainError):
    """No active client matches the organization, certificate and client id of a resolve request."""

    message = "Client authorization does not exist for given parameters"


class CertificateNotFoundError(DomainError):
    message = "Certificate not found"


class CertificatesNotFoundError(DomainError):
    """One or more of the certificates to link to a client do not exist in the organization."""

    message = "Not all requested certificates exists"


class ScopesNotFoundError(DomainError):
    message = "Not all of provided scopes exists"


class PersonalIdTypesNotFoundError(DomainError):
    message = "Not all of provided personal_id_types exists"


class ScopesNotInOrganizationError(DomainError):
    """A client requests scopes its organization has not been granted."""

    def __init__(self, scopes: Sequence[str]) -> None:
        self.scopes = list(scopes)
        super().__init__(f"The following scopes do not exist in the organization: {', '.join(scopes)}")


class PersonalIdTypesNotInOrganizationError(DomainError):
    """A client requests personal id types its organization may not request."""

    def __init__(self, personal_id_types: Sequence[str]) -> None:
        self.personal_id_types = list(personal_id_types)
        super().__init__(
            f"The following Personal id types do not exist in the organization: {', '.join(personal_id_types)}"
        )
