from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from gfmodules.logging.testing import capture_records

from app.container import get_database
from app.logging.events import Log
from app.routers.health import router


def test_an_unhealthy_database_answers_503_and_is_logged() -> None:
    database = MagicMock()
    database.is_healthy.return_value = False
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_database] = lambda: database

    with capture_records("app.routers.health") as captured:
        response = TestClient(app).get("/health")

    assert response.status_code == 503
    unhealthy = [
        entry.record
        for entry in captured.entries
        if getattr(entry.record, "event_id", None) == Log.HEALTH_UNHEALTHY.event_id
    ]
    assert [record.component for record in unhealthy] == ["database"]  # type: ignore[attr-defined]
