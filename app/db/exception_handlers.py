from fastapi import Request
from fastapi.responses import JSONResponse
from psycopg.errors import ForeignKeyViolation, UniqueViolation
from sqlalchemy.exc import IntegrityError


async def translate_integrity_error_handler(
    _: Request,
    exc: IntegrityError,
) -> JSONResponse:
    if (
        isinstance(exc.orig, ForeignKeyViolation)
        and exc.orig.diag
        and exc.orig.diag.constraint_name
        and exc.orig.diag.constraint_name.endswith("_organization_id_fkey")
    ):
        return JSONResponse(status_code=404, content="Organization not found")
    if isinstance(exc.orig, UniqueViolation) and exc.orig.diag and exc.orig.diag.constraint_name:
        return JSONResponse(status_code=409, content="Duplicate entity")

    return JSONResponse(status_code=500, content="Internal Server ErrorRRRRRR!!!")
