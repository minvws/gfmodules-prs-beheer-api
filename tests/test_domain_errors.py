"""The routing layer maps every domain exception to exactly one status code."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from app import application, exceptions
from app.config import set_config
from app.exceptions import DomainError, ScopesNotInOrganizationError
from app.routers.errors import STATUS_CODES, domain_error_handler, install_domain_error_handler, status_code_for
from tests.test_config import get_test_config


def _all_domain_errors() -> list[type[DomainError]]:
    return [
        cls
        for cls in vars(exceptions).values()
        if isinstance(cls, type) and issubclass(cls, DomainError) and cls is not DomainError
    ]


def test_every_domain_error_has_a_status_code() -> None:
    unmapped = [cls.__name__ for cls in _all_domain_errors() if cls not in STATUS_CODES]
    assert unmapped == []


def test_every_mapped_status_code_is_a_client_error() -> None:
    assert all(400 <= code < 500 for code in STATUS_CODES.values())


def test_subclasses_inherit_the_mapping_of_their_parent() -> None:
    class MoreSpecificNotFoundError(exceptions.ClientNotFoundError):
        pass

    assert status_code_for(MoreSpecificNotFoundError()) == 404


def test_unmapped_domain_error_is_an_internal_error() -> None:
    class Unmapped(DomainError):
        pass

    assert status_code_for(Unmapped()) == 500


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    install_domain_error_handler(app)

    @app.get("/refuse")
    def refuse() -> None:
        raise exceptions.OrganizationHasActiveClientsError()

    @app.get("/with-arguments")
    def with_arguments() -> None:
        raise ScopesNotInOrganizationError(["prs:read", "prs:write"])

    @app.get("/custom-message")
    def custom_message() -> None:
        raise exceptions.PersonalIdTypesNotFoundError("Not all of provided receive personal_id_types exists")

    return TestClient(app)


def test_handler_answers_with_the_mapped_code_and_the_message(client: TestClient) -> None:
    response = client.get("/refuse")

    assert response.status_code == 403
    assert response.json() == {"detail": "Organization still has active clients"}


def test_handler_includes_the_arguments_in_the_message(client: TestClient) -> None:
    response = client.get("/with-arguments")

    assert response.status_code == 404
    assert response.json() == {"detail": "The following scopes do not exist in the organization: prs:read, prs:write"}


def test_handler_uses_the_message_given_at_raise_time(client: TestClient) -> None:
    response = client.get("/custom-message")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not all of provided receive personal_id_types exists"}


def test_application_registers_the_domain_error_handler(mocker: MockerFixture) -> None:
    mocker.patch("app.application.container.configure")
    set_config(get_test_config())

    app = application.setup_fastapi()

    assert app.exception_handlers[DomainError] is domain_error_handler
