import logging
from logging.config import dictConfig
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import container
from app.config import get_config
from app.logging.config_builder import LogConfigBuilder
from app.logging.events import Log
from app.logging.middleware import RequestContextMiddleware
from app.middleware.stats import StatsdMiddleware
from app.routers.client import router as client_router
from app.routers.default import router as default_router
from app.routers.health import router as health_router
from app.routers.organization import router as organization_router
from app.routers.resolve import router as resolve_router

logger = logging.getLogger(__name__)


def _error_reason(exc: RequestValidationError) -> str:
    return "; ".join(f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors())


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    body = (await request.body()).decode(errors="replace")
    logger.warning(
        "Request validation failed method=%s path=%s body=%s errors=%s",
        request.method,
        request.url.path,
        body,
        exc.errors(),
    )
    Log.event(
        logger,
        Log.ONBOARDING_VALIDATION_FAILED,
        "validation failed for supplied registration data",
        error_reason=_error_reason(exc),
        endpoint=request.url.path,
    )
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


def get_uvicorn_params() -> dict[str, Any]:
    config = get_config()

    kwargs = {
        "host": config.uvicorn.host,
        "port": config.uvicorn.port,
        "reload": config.uvicorn.reload,
        "reload_delay": config.uvicorn.reload_delay,
        "reload_dirs": config.uvicorn.reload_dirs,
        "factory": True,
    }
    if (
        config.uvicorn.use_ssl
        and config.uvicorn.ssl_base_dir is not None
        and config.uvicorn.ssl_cert_file is not None
        and config.uvicorn.ssl_key_file is not None
    ):
        kwargs["ssl_keyfile"] = config.uvicorn.ssl_base_dir + "/" + config.uvicorn.ssl_key_file
        kwargs["ssl_certfile"] = config.uvicorn.ssl_base_dir + "/" + config.uvicorn.ssl_cert_file
    return kwargs


def run() -> None:
    uvicorn.run("app.application:create_fastapi_app", **get_uvicorn_params())


def create_fastapi_app() -> FastAPI:
    setup_logging()
    fastapi = setup_fastapi()

    return fastapi


def setup_logging() -> None:
    config = get_config()
    loglevel = config.app.loglevel.upper()
    if loglevel not in logging.getLevelNamesMapping():
        raise ValueError(f"Invalid loglevel {loglevel}")

    log_config = LogConfigBuilder(
        loglevel=loglevel,
        logging_config=config.logging,
    ).build()
    dictConfig(log_config)


def setup_fastapi() -> FastAPI:
    config = get_config()

    fastapi = (
        FastAPI(
            docs_url=config.uvicorn.docs_url,
            redoc_url=config.uvicorn.redoc_url,
            title="PRS Beheer API",
            root_path=config.uvicorn.root_path,
        )
        if config.uvicorn.swagger_enabled
        else FastAPI(docs_url=None, redoc_url=None)
    )

    container.configure()

    fastapi.add_middleware(RequestContextMiddleware)

    routers = [default_router, health_router, organization_router, client_router, resolve_router]

    for router in routers:
        fastapi.include_router(router)

    fastapi.exception_handler(RequestValidationError)(request_validation_exception_handler)

    if config.stats.enabled:
        fastapi.add_middleware(StatsdMiddleware, module_name=config.stats.module_name or "default")

    return fastapi
