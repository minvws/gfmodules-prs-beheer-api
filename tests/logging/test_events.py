import pytest
from gfmodules.logging import DefaultEventCatalogue, LoggingStreams, declared_events
from gfmodules.logging.testing import assert_catalogue_complete

from app.logging.events import ACT_CN, Log

_APP = LoggingStreams.APP
_SIEM = LoggingStreams.SIEM


class TestCatalogue:
    def test_defines_every_required_event(self) -> None:
        assert_catalogue_complete(Log)

    @pytest.mark.parametrize(
        "name,event_id",
        [
            ("ORGANIZATION_REGISTERED", "260400"),
            ("ORGANIZATION_WITHDRAWN", "260401"),
            ("CLIENT_REGISTERED", "260402"),
            ("CLIENT_WITHDRAWN", "260403"),
            ("SCOPES_CHANGED", "260404"),
            ("ONBOARDING_VALIDATION_FAILED", "260405"),
            ("ACCESS_REQUEST", "260450"),
            ("SYS_APP_STARTED", "270401"),
            ("SYS_APP_STOPPED", "270402"),
            ("SYS_APP_CRASHED", "270402"),
            ("SYS_UNHANDLED_EXCEPTION", "270404"),
            ("SYS_MISSING_CORRELATION_ID", "270407"),
        ],
    )
    def test_carries_the_event_id_the_spec_assigns(self, name: str, event_id: str) -> None:
        assert getattr(Log, name).event_id == event_id

    def test_every_declared_event_routes_at_least_one_stream(self) -> None:
        for name, event in declared_events(Log):
            assert event.streams, f"{name} declares no stream"

    def test_every_allow_list_names_a_stream_the_event_routes(self) -> None:
        for name, event in declared_events(Log):
            unrouted = set(event.fields) - set(event.streams)
            assert not unrouted, f"{name} allow-lists fields for streams it does not route: {unrouted}"

    def test_no_event_routes_to_public_inspect(self) -> None:
        for name, event in declared_events(Log):
            assert LoggingStreams.PUBLIC_INSPECT not in event.streams, f"{name} routes to public_inspect"


class TestPerRouteAccessIds:
    def test_the_beheer_routes_carry_their_own_access_event_id(self) -> None:
        assert Log.access_event_id[("POST", "/organizations")] == "260700"
        assert Log.access_event_id[("DELETE", "/organizations/{organization_id}/clients/{id}")] == "260705"


class TestTheOverriddenSlots:
    def test_the_access_record_adds_the_acting_client_and_drops_the_body(self) -> None:
        allowed = set(Log.ACCESS_REQUEST.fields[_APP])

        assert ACT_CN.name in allowed
        assert "body" not in allowed
        assert "body_truncated" not in allowed

    def test_every_other_system_slot_keeps_the_shared_routing(self) -> None:
        rerouted = {
            name
            for name, event in vars(Log).items()
            if not name.startswith("_")
            and name in vars(DefaultEventCatalogue)
            and isinstance(getattr(DefaultEventCatalogue, name, None), type(Log.SYS_APP_STARTED))
            and event.replace(event_id="") != getattr(DefaultEventCatalogue, name)
        }
        assert rerouted == {"ACCESS_REQUEST"}
