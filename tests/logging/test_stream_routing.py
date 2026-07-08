"""Verifies per-field stream routing (APP == stroom 2, SIEM == stroom 3) for the PRS-OB events."""

import io
import json
import logging
from typing import Any, Iterator

import pytest

from app.logging.context import endpoint_var, ip_var, method_var, request_id_var
from app.logging.events import Log
from app.logging.filters import AppFilter, LoggingStreams, SiemFilter
from app.logging.formatter import JsonFormatter


@pytest.fixture
def streams() -> Iterator[tuple[logging.Logger, io.StringIO, io.StringIO]]:
    app_buf, siem_buf = io.StringIO(), io.StringIO()

    app_handler = logging.StreamHandler(app_buf)
    app_handler.addFilter(AppFilter())
    app_handler.setFormatter(JsonFormatter(include_traces=False, stream=LoggingStreams.APP, stream_id="app"))

    siem_handler = logging.StreamHandler(siem_buf)
    siem_handler.addFilter(SiemFilter())
    siem_handler.setFormatter(JsonFormatter(include_traces=False, stream=LoggingStreams.SIEM, stream_id="siem"))

    logger = logging.getLogger("app.test_stream_routing")
    logger.setLevel(logging.DEBUG)
    logger.handlers = [app_handler, siem_handler]
    logger.propagate = False

    tokens = [
        request_id_var.set("req-1"),
        ip_var.set("10.0.0.1"),
        endpoint_var.set("/organizations"),
        method_var.set("POST"),
    ]
    try:
        yield logger, app_buf, siem_buf
    finally:
        logger.handlers = []
        request_id_var.reset(tokens[0])
        ip_var.reset(tokens[1])
        endpoint_var.reset(tokens[2])
        method_var.reset(tokens[3])


def _records(buf: io.StringIO) -> list[dict[str, Any]]:
    return [json.loads(line) for line in buf.getvalue().splitlines()]


def _messages(buf: io.StringIO) -> list[dict[str, Any]]:
    return [record["message"] for record in _records(buf)]


def test_records_carry_stream_id(streams: tuple[logging.Logger, io.StringIO, io.StringIO]) -> None:
    logger, app_buf, siem_buf = streams
    Log.event(logger, Log.ORGANIZATION_REGISTERED, "registered", organisatie_oin="00000099000000001000")

    assert _records(app_buf)[0]["stream_id"] == "app"
    assert _records(siem_buf)[0]["stream_id"] == "siem"


def test_organization_registered_withholds_bevoegdheden_from_siem(
    streams: tuple[logging.Logger, io.StringIO, io.StringIO],
) -> None:
    logger, app_buf, siem_buf = streams
    Log.event(
        logger,
        Log.ORGANIZATION_REGISTERED,
        "registered",
        organisatie_oin="00000099000000001000",
        bevoegdheden="read write",
    )

    app_msg = _messages(app_buf)[0]
    siem_msg = _messages(siem_buf)[0]

    assert app_msg["bevoegdheden"] == "read write"
    assert "bevoegdheden" not in siem_msg  # not in SIEM allow-list for PRS-OB-001
    for msg in (app_msg, siem_msg):
        assert msg["organisatie_oin"] == "00000099000000001000"


def test_client_registered_withholds_common_name_from_siem(
    streams: tuple[logging.Logger, io.StringIO, io.StringIO],
) -> None:
    logger, app_buf, siem_buf = streams
    Log.event(
        logger,
        Log.CLIENT_REGISTERED,
        "registered",
        organisatie_oin="00000099000000001000",
        handelende_oin="00000099000000002000",
        common_name="client.example.com",
        scopes="read",
    )

    app_msg = _messages(app_buf)[0]
    siem_msg = _messages(siem_buf)[0]

    assert app_msg["common_name"] == "client.example.com"
    assert "common_name" not in siem_msg  # not in SIEM allow-list for PRS-OB-003
    for msg in (app_msg, siem_msg):
        assert msg["organisatie_oin"] == "00000099000000001000"
        assert msg["handelende_oin"] == "00000099000000002000"
        assert msg["scopes"] == "read"


def test_validation_failed_withholds_endpoint_from_siem(
    streams: tuple[logging.Logger, io.StringIO, io.StringIO],
) -> None:
    logger, app_buf, siem_buf = streams
    Log.event(
        logger,
        Log.ONBOARDING_VALIDATION_FAILED,
        "validation failed",
        error_reason="register_id: invalid OIN",
        endpoint="/organizations",
    )

    app_msg = _messages(app_buf)[0]
    siem_msg = _messages(siem_buf)[0]

    assert app_msg["endpoint"] == "/organizations"
    assert "endpoint" not in siem_msg  # not in SIEM allow-list for PRS-OB-006
    for msg in (app_msg, siem_msg):
        assert msg["error_reason"] == "register_id: invalid OIN"
