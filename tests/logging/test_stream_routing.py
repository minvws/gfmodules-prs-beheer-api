import logging
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from typing import Any

import gfmodules.logging as gflog
import pytest
from gfmodules.logging import LogEvent, LoggingStreams, bind_context
from gfmodules.logging.testing import assert_fields_absent, capture_stream

from app.logging.events import Log

_LOGGER_NAME = "app.test_stream_routing"
_ORGANISATIE_OIN = "00000099000000001000"
_HANDELENDE_OIN = "00000099000000002000"

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
            "gf-act-cn": "acting-client",
        }
    ):
        yield _route


class TestOrganizationRegistered:
    @pytest.fixture
    def routed(self, route: Route) -> Routed:
        return route(
            Log.ORGANIZATION_REGISTERED,
            "registered",
            organisatie_oin=_ORGANISATIE_OIN,
            bevoegdheden="read write",
        )

    def test_both_streams_receive_the_organisatie_oin(self, routed: Routed) -> None:
        assert routed[LoggingStreams.APP][0]["organisatie_oin"] == _ORGANISATIE_OIN
        assert routed[LoggingStreams.SIEM][0]["organisatie_oin"] == _ORGANISATIE_OIN

    def test_siem_does_not_receive_the_bevoegdheden(self, routed: Routed) -> None:
        assert routed[LoggingStreams.APP][0]["bevoegdheden"] == "read write"
        assert_fields_absent(routed[LoggingStreams.SIEM], "bevoegdheden")

    def test_public_inspect_receives_nothing(self, routed: Routed) -> None:
        assert routed[LoggingStreams.PUBLIC_INSPECT] == []


class TestClientRegistered:
    @pytest.fixture
    def routed(self, route: Route) -> Routed:
        return route(
            Log.CLIENT_REGISTERED,
            "registered",
            organisatie_oin=_ORGANISATIE_OIN,
            handelende_oin=_HANDELENDE_OIN,
            common_name="client.example.com",
            scopes="read",
        )

    def test_siem_does_not_receive_the_common_name(self, routed: Routed) -> None:
        assert routed[LoggingStreams.APP][0]["common_name"] == "client.example.com"
        assert_fields_absent(routed[LoggingStreams.SIEM], "common_name")

    def test_both_streams_receive_the_oins_and_scopes(self, routed: Routed) -> None:
        for message in (routed[LoggingStreams.APP][0], routed[LoggingStreams.SIEM][0]):
            assert message["organisatie_oin"] == _ORGANISATIE_OIN
            assert message["handelende_oin"] == _HANDELENDE_OIN
            assert message["scopes"] == "read"


class TestOnboardingValidationFailed:
    @pytest.fixture
    def routed(self, route: Route) -> Routed:
        return route(
            Log.ONBOARDING_VALIDATION_FAILED,
            "validation failed",
            error_reason="register_id: invalid OIN",
            endpoint="/organizations",
        )

    def test_siem_does_not_receive_the_endpoint(self, routed: Routed) -> None:
        assert routed[LoggingStreams.APP][0]["endpoint"] == "/organizations"
        assert_fields_absent(routed[LoggingStreams.SIEM], "endpoint")

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

    def test_carries_the_acting_client_and_the_response(self, routed: Routed) -> None:
        message = routed[LoggingStreams.APP][0]

        assert message["gf-act-cn"] == "acting-client"
        assert message["status_code"] == 201
        assert message["duration_ms"] == 5


class TestCorrelationMetadata:
    def test_is_retained_in_every_routed_stream(self, route: Route) -> None:
        routed = route(Log.ORGANIZATION_REGISTERED, "registered", organisatie_oin=_ORGANISATIE_OIN)

        for stream in (LoggingStreams.APP, LoggingStreams.SIEM):
            message = routed[stream][0]
            assert message["request_id"] == "req-1"
            assert message["correlation_id"] == "corr-1"
            assert message["ip"] == "10.0.0.1"
