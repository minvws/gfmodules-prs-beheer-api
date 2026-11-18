import logging
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from typing import Any

import gfmodules.logging as gflog
import pytest
from gfmodules.logging import LogEvent, LoggingStreams, bind_context
from gfmodules.logging.testing import assert_fields_absent, capture_stream

from app.logging.context import (
    ACTING_ORGANIZATION_IDENTIFIERS,
    ACTOR,
    CLIENT_NAME,
    NAMES,
    REPRESENTED_ORGANIZATION_IDENTIFIER,
    REPRESENTED_ORGANIZATION_NAME,
)
from app.logging.events import Log

_LOGGER_NAME = "app.test_stream_routing"
_REPRESENTED_OIN = "00000099000000001000"
_ACTING_OIN = "00000099000000002000"
_ACTOR = "admin.example.com"
_ORGANIZATION_NAME = "Example Organization"
_CLIENT_NAME = "Example Client"
_IDENTIFIERS = {
    ACTOR.name: _ACTOR,
    REPRESENTED_ORGANIZATION_IDENTIFIER.name: _REPRESENTED_OIN,
    ACTING_ORGANIZATION_IDENTIFIERS.name: _ACTING_OIN,
}
_BOUND_NAMES = {
    REPRESENTED_ORGANIZATION_NAME.name: _ORGANIZATION_NAME,
    CLIENT_NAME.name: _CLIENT_NAME,
}

Routed = dict[LoggingStreams, list[dict[str, Any]]]
Route = Callable[..., Routed]


@pytest.fixture
def route() -> Iterator[Route]:
    logger = logging.getLogger(_LOGGER_NAME)

    def _route(event: LogEvent, message: str = "event", **fields: Any) -> Routed:
        with ExitStack() as stack:
            routed: Routed = {
                stream: stack.enter_context(capture_stream(stream, _LOGGER_NAME)) for stream in LoggingStreams
            }
            gflog.emit(logger, event, message, fields={**fields})
        return routed

    with bind_context(
        {
            "request_id": "req-1",
            "ip": "10.0.0.1",
            "endpoint": "/organizations",
            "method": "POST",
            "correlation_id": "corr-1",
            **_IDENTIFIERS,
            **_BOUND_NAMES,
        }
    ):
        yield _route


class TestAuditEvents:
    def test_identifiers_reach_both_streams_and_names_only_the_app_stream(self, route: Route) -> None:
        for event, fields in (
            (Log.ORGANIZATION_REGISTERED, {"scopes": ["read"]}),
            (Log.ORGANIZATION_WITHDRAWN, {}),
            (Log.CLIENT_REGISTERED, {"common_name": ["client.example.com"], "scopes": ["read"]}),
            (Log.CLIENT_WITHDRAWN, {}),
            (Log.SCOPES_CHANGED, {"changed_scopes": ["read"]}),
            (Log.ONBOARDING_VALIDATION_FAILED, {"error_reason": "invalid"}),
        ):
            routed = route(event, **fields)
            app, siem = routed[LoggingStreams.APP][0], routed[LoggingStreams.SIEM][0]

            for message in (app, siem):
                for name, value in _IDENTIFIERS.items():
                    assert message[name] == value
            for name in NAMES:
                assert app[name] == _BOUND_NAMES[name]
            assert_fields_absent([siem], *NAMES)

    def test_each_event_routes_only_its_own_data(self, route: Route) -> None:
        client = route(Log.CLIENT_REGISTERED, common_name=["client.example.com"], scopes=["read"])
        assert client[LoggingStreams.APP][0]["common_name"] == ["client.example.com"]
        assert_fields_absent(client[LoggingStreams.SIEM], "common_name")
        assert client[LoggingStreams.APP][0]["scopes"] == ["read"]
        assert client[LoggingStreams.SIEM][0]["scopes"] == ["read"]

        organization = route(Log.ORGANIZATION_REGISTERED, scopes=["read"])
        assert organization[LoggingStreams.APP][0]["scopes"] == ["read"]
        assert_fields_absent(organization[LoggingStreams.SIEM], "scopes")


class TestOnboardingValidationFailed:
    @pytest.fixture
    def routed(self, route: Route) -> Routed:
        return route(
            Log.ONBOARDING_VALIDATION_FAILED,
            "validation failed",
            error_reason="register_id: invalid OIN",
        )

    def test_both_streams_receive_the_endpoint(self, routed: Routed) -> None:
        assert routed[LoggingStreams.APP][0]["endpoint"] == "/organizations"
        assert routed[LoggingStreams.SIEM][0]["endpoint"] == "/organizations"

    def test_both_streams_receive_the_error_reason(self, routed: Routed) -> None:
        assert routed[LoggingStreams.APP][0]["error_reason"] == "register_id: invalid OIN"
        assert routed[LoggingStreams.SIEM][0]["error_reason"] == "register_id: invalid OIN"


class TestAccessRequest:
    @pytest.fixture
    def routed(self, route: Route) -> Routed:
        return route(Log.ACCESS_REQUEST, "access", status_code=201, duration_ms=5)

    def test_reaches_the_app_stream_only(self, routed: Routed) -> None:
        assert routed[LoggingStreams.SIEM] == []
        assert routed[LoggingStreams.PUBLIC_INSPECT] == []

    def test_carries_the_response(self, routed: Routed) -> None:
        message = routed[LoggingStreams.APP][0]

        assert message["status_code"] == 201
        assert message["duration_ms"] == 5


class TestCorrelationMetadata:
    def test_is_retained_in_every_routed_stream(self, route: Route) -> None:
        routed = route(Log.ORGANIZATION_REGISTERED, "registered", scopes=["read"])

        for stream in (LoggingStreams.APP, LoggingStreams.SIEM):
            message = routed[stream][0]
            assert message["request_id"] == "req-1"
            assert message["correlation_id"] == "corr-1"
            assert message["ip"] == "10.0.0.1"
