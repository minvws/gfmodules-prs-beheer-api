import logging
from collections.abc import Mapping
from typing import ClassVar

from gfmodules.logging import ContextField, DefaultEventCatalogue, LogEvent, LoggingStreams
from gfmodules.logging.context import sanitize_free_text

_APP = LoggingStreams.APP
_SIEM = LoggingStreams.SIEM

_Base = DefaultEventCatalogue

ACTOR = ContextField(name="actor_cn", header="x-gf-act-cn", sanitizer=sanitize_free_text)
ORGANIZATION = ContextField(name="organization_id", header=None)
_REQUESTER = (ACTOR.name, ORGANIZATION.name)


class Log(_Base):
    context_fields = (ACTOR, ORGANIZATION)

    ORGANIZATION_REGISTERED = LogEvent(  # PRS-OB-001
        "260400",
        logging.INFO,
        (_APP, _SIEM),
        {
            _APP: (*_REQUESTER, "organization_identifier", "scopes"),
            _SIEM: (*_REQUESTER, "organization_identifier"),
        },
    )
    ORGANIZATION_WITHDRAWN = LogEvent(  # PRS-OB-002
        "260401",
        logging.WARNING,
        (_APP, _SIEM),
        {
            _APP: (*_REQUESTER, "organization_identifier"),
            _SIEM: (*_REQUESTER, "organization_identifier"),
        },
    )
    CLIENT_REGISTERED = LogEvent(  # PRS-OB-003
        "260402",
        logging.INFO,
        (_APP, _SIEM),
        {
            _APP: (
                *_REQUESTER,
                "organization_identifier",
                "acting_organization_identifiers",
                "common_name",
                "scopes",
            ),
            _SIEM: (*_REQUESTER, "acting_organization_identifiers", "organization_identifier", "scopes"),
        },
    )
    CLIENT_WITHDRAWN = LogEvent(  # PRS-OB-004
        "260403",
        logging.WARNING,
        (_APP, _SIEM),
        {
            _APP: (*_REQUESTER, "acting_organization_identifiers", "organization_identifier"),
            _SIEM: (*_REQUESTER, "acting_organization_identifiers"),
        },
    )
    SCOPES_CHANGED = LogEvent(  # PRS-OB-005
        "260404",
        logging.WARNING,
        (_APP, _SIEM),
        {
            _APP: (*_REQUESTER, "organization_identifier", "acting_organization_identifiers", "changed_scopes"),
            _SIEM: (*_REQUESTER, "organization_identifier", "acting_organization_identifiers"),
        },
    )
    ONBOARDING_VALIDATION_FAILED = LogEvent(  # PRS-OB-006
        "260405",
        logging.WARNING,
        (_APP, _SIEM),
        {
            _APP: (*_REQUESTER, "error_reason"),
            _SIEM: (*_REQUESTER, "error_reason"),
        },
    )
    HEALTH_UNHEALTHY = LogEvent(  # PRS-HEALTH-001
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
    SYS_UNHANDLED_EXCEPTION = _Base.SYS_UNHANDLED_EXCEPTION.with_id("270404").add_fields(  # PRS-SYS-004
        {_APP: _REQUESTER, _SIEM: _REQUESTER}
    )
    SYS_MISSING_CORRELATION_ID = _Base.SYS_MISSING_CORRELATION_ID.with_id("270428")
    ACCESS_REQUEST = _Base.ACCESS_REQUEST.add_fields({_APP: _REQUESTER})

    access_event_id: ClassVar[Mapping[tuple[str, str], str]] = {
        ("POST", "/organizations"): "260700",
        ("PUT", "/organizations/{id}"): "260701",
        ("DELETE", "/organizations/{id}"): "260702",
        ("POST", "/organizations/{organization_id}/clients"): "260703",
        ("PUT", "/organizations/{organization_id}/clients/{id}"): "260704",
        ("DELETE", "/organizations/{organization_id}/clients/{id}"): "260705",
    }
