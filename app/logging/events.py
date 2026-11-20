import logging
from typing import ClassVar

from gfmodules.logging import ContextField, DefaultEventCatalogue, LogEvent, LoggingStreams

from app.logging.context import CONTEXT_FIELDS, NAMES

_APP = LoggingStreams.APP
_SIEM = LoggingStreams.SIEM

_Base = DefaultEventCatalogue


def _audit(event_id: str, level: int, app: tuple[str, ...] = (), siem: tuple[str, ...] = ()) -> LogEvent:
    return LogEvent(event_id, level, (_APP, _SIEM), {_APP: (*NAMES, *app), _SIEM: siem})


class Log(_Base):
    ORGANIZATION_REGISTERED = _audit("260400", logging.INFO, app=("scopes",))
    ORGANIZATION_WITHDRAWN = _audit("260401", logging.WARNING)
    CLIENT_REGISTERED = _audit("260402", logging.INFO, app=("common_name", "scopes"), siem=("scopes",))
    CLIENT_WITHDRAWN = _audit("260403", logging.WARNING)
    SCOPES_CHANGED = _audit("260404", logging.WARNING, app=("changed_scopes",))
    ONBOARDING_VALIDATION_FAILED = _audit("260405", logging.WARNING, app=("error_reason",), siem=("error_reason",))
    HEALTH_UNHEALTHY = LogEvent(
        "270400",
        logging.ERROR,
        (_APP, _SIEM),
        {_APP: ("component", "status", "error_detail"), _SIEM: ("component", "status")},
    )
    SYS_APP_STARTED = _Base.SYS_APP_STARTED.with_id("270401")  # PRS-SYS-001
    SYS_APP_STOPPED = _Base.SYS_APP_STOPPED.with_id("270402")  # PRS-SYS-002
    SYS_APP_CRASHED = _Base.SYS_APP_CRASHED.with_id("270402")  # PRS-SYS-002
    SYS_DB_CONNECTION_FAILED = LogEvent(
        "270403",
        logging.ERROR,
        (_APP, _SIEM),
        {_APP: ("error_type", "retry_attempt", "backoff_seconds"), _SIEM: ("error_type",)},
    )
    SYS_UNHANDLED_EXCEPTION = _Base.SYS_UNHANDLED_EXCEPTION.with_id("270404").add_fields({_APP: NAMES})
    SYS_MISSING_CORRELATION_ID = _Base.SYS_MISSING_CORRELATION_ID.with_id("270428")

    ACCESS_REQUEST = _Base.ACCESS_REQUEST.add_fields({_APP: NAMES})

    context_fields: ClassVar[tuple[ContextField, ...]] = CONTEXT_FIELDS
