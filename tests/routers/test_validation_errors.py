from fastapi.testclient import TestClient
from gfmodules.logging.testing import capture_records

from app.logging.events import Log

REJECTED_OIN = "secret-input-value"


def test_a_validation_failure_logs_where_and_why_without_the_rejected_input(api: TestClient) -> None:
    with capture_records("app.application") as captured:
        response = api.post(
            "/organizations",
            json={
                "external_id": REJECTED_OIN,
                "name": "Org",
                "scopes": [],
                "receive_personal_id_types": [],
                "request_personal_id_types": [],
            },
        )

    assert response.status_code == 422
    reasons = [
        entry.record.error_reason  # type: ignore[attr-defined]
        for entry in captured.entries
        if getattr(entry.record, "event_id", None) == Log.ONBOARDING_VALIDATION_FAILED.event_id
    ]
    assert reasons == ["body.external_id: value_error"]
    assert all(REJECTED_OIN not in entry.record.getMessage() for entry in captured.entries)
