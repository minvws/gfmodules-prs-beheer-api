"""
Maps domain exceptions to HTTP responses.

This is the only place where a domain error becomes a status code. Services
raise the exceptions from ``app/exceptions.py``; the handler registered here
turns them into the same ``{"detail": ...}`` body FastAPI uses for
``HTTPException``.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    CertificateNotFoundError,
    CertificatesNotFoundError,
    ClientAuthorizationNotFoundError,
    ClientNotFoundError,
    DomainError,
    OrganizationHasActiveClientsError,
    OrganizationNotFoundError,
    PersonalIdTypesNotFoundError,
    PersonalIdTypesNotInOrganizationError,
    ScopesNotFoundError,
    ScopesNotInOrganizationError,
)

logger = logging.getLogger(__name__)

STATUS_CODES: dict[type[DomainError], int] = {
    OrganizationNotFoundError: 404,
    OrganizationHasActiveClientsError: 403,
    ClientNotFoundError: 404,
    ClientAuthorizationNotFoundError: 404,
    CertificateNotFoundError: 404,
    CertificatesNotFoundError: 404,
    ScopesNotFoundError: 404,
    PersonalIdTypesNotFoundError: 404,
    ScopesNotInOrganizationError: 404,
    PersonalIdTypesNotInOrganizationError: 404,
}


def status_code_for(exc: DomainError) -> int:
    for cls in type(exc).__mro__:
        if cls in STATUS_CODES:
            return STATUS_CODES[cls]
    logger.error("no status code mapped for %s", type(exc).__name__)
    return 500


def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    status_code = status_code_for(exc)
    logger.warning(
        "%s %s refused with %d: %s",
        request.method,
        request.url.path,
        status_code,
        exc.message,
    )
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


def install_domain_error_handler(fastapi: FastAPI) -> None:
    fastapi.add_exception_handler(DomainError, domain_error_handler)
