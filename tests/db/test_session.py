from collections.abc import Callable, Sequence
from typing import Any
from unittest.mock import patch

import pytest
from gfmodules.logging.testing import assert_event_emitted, capture_records
from pydantic import SecretStr
from sqlalchemy import select, text
from sqlalchemy.exc import DatabaseError, OperationalError, PendingRollbackError

from app.config import ConfigDatabase
from app.db.db import Database
from app.db.models.organization import OrganizationEntity
from app.logging.events import Log
from tests.conftest import TEST_EXTERNAL_ID, TEST_ORG_NAME


def _failing(*errors: Exception) -> Callable[..., Any]:
    """A callable raising each error in turn, then succeeding."""
    remaining: list[Exception] = list(errors)

    def call(*_args: Any, **_kwargs: Any) -> None:
        if remaining:
            raise remaining.pop(0)

    return call


@pytest.fixture()
def retrying_database() -> Database:
    """A database with a non-empty backoff, so the retry loop is actually exercised."""
    database = Database(config_database=ConfigDatabase(dsn=SecretStr("sqlite:///:memory:"), retry_backoff=[0.01, 0.01]))
    with database.get_db_session(commit=True) as session:
        session.session.execute(text("ATTACH DATABASE ':memory:' as admin"))
        session.session.execute(text("ATTACH DATABASE ':memory:' as prs"))
    database.generate_tables()
    return database


def test_commit_failure_is_not_masked_by_retry(retrying_database: Database) -> None:
    """
    A failed flush poisons the transaction and the rollback that clears it discards the
    staged entity. Retrying the commit would then succeed against an empty session and
    report success while nothing was written -- it must raise instead.
    """
    with retrying_database.get_db_session() as session:
        session.add(OrganizationEntity(external_id=TEST_EXTERNAL_ID, name=TEST_ORG_NAME))

        flaky = _failing(
            OperationalError("stmt", {}, Exception("connection refused")),
            PendingRollbackError("transaction has been rolled back"),
        )
        with patch.object(session.session, "commit", side_effect=flaky) as commit, pytest.raises(DatabaseError):
            session.commit()

        assert commit.call_count == 1, "commit must not be retried once its unit of work is lost"


def test_commit_failure_leaves_nothing_persisted(retrying_database: Database) -> None:
    """The insert must be absent afterwards -- and the caller must have been told."""
    with retrying_database.get_db_session() as session:
        session.add(OrganizationEntity(external_id=TEST_EXTERNAL_ID, name=TEST_ORG_NAME))

        flaky = _failing(OperationalError("stmt", {}, Exception("connection refused")))
        with (
            capture_records("app") as records,
            patch.object(session.session, "commit", side_effect=flaky),
            pytest.raises(DatabaseError),
        ):
            session.commit()

    assert_event_emitted(records, Log.SYS_DB_CONNECTION_FAILED, error_type="OperationalError")
    with retrying_database.get_db_session() as session:
        rows: Sequence[Any] = session.execute(select(OrganizationEntity)).scalars().all()
        assert rows == []


def test_every_connection_failure_on_a_read_is_logged_with_its_backoff(retrying_database: Database) -> None:
    with retrying_database.get_db_session() as session, capture_records("app") as records:
        failures = [OperationalError("stmt", {}, Exception("connection refused")) for _ in range(3)]
        with patch.object(session.session, "execute", side_effect=_failing(*failures)), pytest.raises(DatabaseError):
            session.execute(select(OrganizationEntity))

    attempts = [
        (entry.message["error_type"], entry.message["retry_attempt"], entry.message["backoff_seconds"])
        for entry in records.for_event(Log.SYS_DB_CONNECTION_FAILED)
    ]
    assert attempts == [("OperationalError", 1, 0.01), ("OperationalError", 2, 0.01), ("OperationalError", 3, 0)]


def test_reads_are_still_retried_after_a_rollback() -> None:
    """Rollback-and-retry remains valid recovery for statements that re-run from scratch."""
    database = Database(config_database=ConfigDatabase(dsn=SecretStr("sqlite:///:memory:"), retry_backoff=[0.01]))
    with database.get_db_session(commit=True) as session:
        session.session.execute(text("ATTACH DATABASE ':memory:' as admin"))
        session.session.execute(text("ATTACH DATABASE ':memory:' as prs"))
    database.generate_tables()

    with database.get_db_session() as session:
        real_execute = session.session.execute
        flaky = [PendingRollbackError("transaction has been rolled back")]

        def execute(*args: Any, **kwargs: Any) -> Any:
            if flaky:
                raise flaky.pop(0)
            return real_execute(*args, **kwargs)

        with patch.object(session.session, "execute", side_effect=execute):
            rows: Sequence[Any] = session.execute(select(OrganizationEntity)).scalars().all()

        assert rows == []
        assert not flaky, "the read should have been retried after the rollback"
