import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.logging.filters import LoggingStreams

_APP = LoggingStreams.APP
_SIEM = LoggingStreams.SIEM


@dataclass(frozen=True)
class LogEvent:
    event_id: str
    level: int
    streams: tuple[LoggingStreams, ...]
    # Per-stream allow-list of field names. APP == "stroom 2", SIEM == "stroom 3".
    # When empty, no per-field routing is applied and every field is sent to all
    # streams in ``streams``.
    fields: Mapping[LoggingStreams, tuple[str, ...]] = field(default_factory=dict)


class Log:
    # Onboarding en Beheer (PRS-OB) audit events for the beheer API.
    # See https://github.com/minvws/gfmodules-coordination-private/issues/1040
    # The ``fields`` map mirrors the "Stroom 2" (APP) / "Stroom 3" (SIEM) columns.
    # The initiated_by/approved_by/deactivated_by/changed_by fields are part of
    # the spec (four-eyes workflow) but the API carries no administrator
    # identity yet; they are routed when supplied.
    ORGANIZATION_REGISTERED = LogEvent(  # PRS-OB-001
        "260400",
        logging.INFO,
        (_APP, _SIEM),
        {
            _APP: ("organisatie_oin", "bevoegdheden", "initiated_by", "approved_by"),
            _SIEM: ("organisatie_oin", "approved_by"),
        },
    )
    ORGANIZATION_WITHDRAWN = LogEvent(  # PRS-OB-002
        "260401",
        logging.WARNING,
        (_APP, _SIEM),
        {
            _APP: ("organisatie_oin", "deactivated_by", "reason"),
            _SIEM: ("organisatie_oin", "deactivated_by"),
        },
    )
    CLIENT_REGISTERED = LogEvent(  # PRS-OB-003
        "260402",
        logging.INFO,
        (_APP, _SIEM),
        {
            _APP: ("organisatie_oin", "handelende_oin", "common_name", "scopes", "approved_by"),
            _SIEM: ("handelende_oin", "organisatie_oin", "scopes"),
        },
    )
    CLIENT_WITHDRAWN = LogEvent(  # PRS-OB-004
        "260403",
        logging.WARNING,
        (_APP, _SIEM),
        {
            _APP: ("handelende_oin", "organisatie_oin", "deactivated_by", "reason"),
            _SIEM: ("handelende_oin", "deactivated_by"),
        },
    )
    SCOPES_CHANGED = LogEvent(  # PRS-OB-005
        "260404",
        logging.WARNING,
        (_APP, _SIEM),
        {
            _APP: ("organisatie_oin", "handelende_oin", "changed_scopes", "changed_by"),
            _SIEM: ("organisatie_oin", "handelende_oin", "changed_by"),
        },
    )
    ONBOARDING_VALIDATION_FAILED = LogEvent(  # PRS-OB-006
        "260405",
        logging.WARNING,
        (_APP, _SIEM),
        {
            _APP: ("error_reason", "endpoint"),
            _SIEM: ("error_reason",),
        },
    )

    @staticmethod
    def event(
        logger: logging.Logger,
        event: LogEvent,
        message: str,
        *,
        exc_info: Any = None,
        **fields: Any,
    ) -> None:
        extra: dict[str, Any] = {
            "event_id": event.event_id,
            "stream": list(event.streams),
        }
        if event.fields:
            extra["field_streams"] = event.fields
        extra.update(fields)
        logger.log(event.level, message, extra=extra, exc_info=exc_info)
