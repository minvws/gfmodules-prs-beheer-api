from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from psycopg.errors import ForeignKeyViolation
from fastapi import HTTPException, Request


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
    return JSONResponse(status_code=500, content="Internal Server Error")
