import pytest
from pydantic import ValidationError

from app.models.client import ClientCreate, ClientUpdate
from app.models.oin import Oin

VALID_PEM_CERT = """-----BEGIN CERTIFICATE-----
MIICqjCCAZKgAwIBAgIUIAHT8cLrfLqmqygl0VALIgRzEPcwDQYJKoZIhvcNAQEL
BQAwDzENMAsGA1UEAwwEdGVzdDAeFw0yNDAxMDEwMDAwMDBaFw0zMDAxMDEwMDAw
MDBaMA8xDTALBgNVBAMMBHRlc3QwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQDQpsb1B2BaPzR3/OGtrYuPtqjUvsHRoobRTYkPvsFxJ94s6knftaK8dItS
0LdteUaekYH/HIh6yIytvUwYyaael4vOEg7YRRNsKGlYPsJn8yLxyO0DeE/lLCaN
m+IYgkaBxv8YHTM2dFsfcODsrFcl2gkFvgHWaYdP7M6T3m82AIsWWX19VcD2O7Sk
nCq87eKSaL4TU3PyPEVX4Scw0ZAD7X6sZXMSXyob13Ga/Zfv+1ld/gRxXmAkM5ux
1zZBlNXLbcEPLnheHSobsV8MKZ6Zx/pIQYlOe8NEP5QOgOvJrU9u2pxcVcAijEht
Up3aXlfwFiLktXw7PbL7+ce7puuRAgMBAAEwDQYJKoZIhvcNAQELBQADggEBACps
/IFk+ye5jmlL6IY9nSTc/YDVwr0MzCFDvgbTxoudUYtypoV5cgH3R+SRTnDZLAx7
3oY0v+Dy2HWKtBk4FjIlvbFJiBqjYlEl9G/Nd8lYcVbG/AQoCDEHwmiuZHXnyMsR
YOdtRWLgtMBIzOhekINMeXHremFOVsL3ZvyX27mcKZQasg8Ekwg+aXjnQVsaZUSn
1xGo07HHTrzGMmOe302JxC75VEp5wNjX1Fyq1/udpLKliB3PqeyUlmcRCNOkUsaw
7r9IJxBe2H+9iduJKCfcAk2DIrcahS2NEOi7ZcyhtV/mus1+mbTdfwbcQCrFWC2p
QU4s4T+D/W6b8luriaw=
-----END CERTIFICATE-----"""


def test_create_should_succeed() -> None:
    model = ClientCreate(oin=Oin("00000099000000001000"), common_name="Test Client")
    assert str(model.oin) == "00000099000000001000"
    assert model.common_name == "Test Client"
    assert model.certificate is None
    assert model.allowed_scopes is None


def test_create_with_certificate_and_allowed_scopes_should_succeed() -> None:
    model = ClientCreate(
        oin=Oin("00000099000000001000"),
        common_name="Test Client",
        certificate=VALID_PEM_CERT,
        allowed_scopes="scope:read scope:write",
    )
    assert model.certificate == VALID_PEM_CERT
    assert model.allowed_scopes == "scope:read scope:write"


def test_create_with_invalid_certificate_should_raise() -> None:
    with pytest.raises(ValidationError, match="valid PEM"):
        ClientCreate(
            oin=Oin("00000099000000001000"),
            common_name="Test Client",
            certificate="not-a-pem",
        )


def test_create_missing_oin_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientCreate(common_name="Test Client")  # type: ignore[call-arg]


def test_create_missing_common_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientCreate(oin=Oin("00000099000000001000"))  # type: ignore[call-arg]


def test_update_should_succeed() -> None:
    model = ClientUpdate(common_name="New Name")
    assert model.common_name == "New Name"
    assert model.certificate is None
    assert model.allowed_scopes is None


def test_update_with_certificate_and_allowed_scopes_should_succeed() -> None:
    model = ClientUpdate(
        common_name="New Name",
        certificate=VALID_PEM_CERT,
        allowed_scopes="scope:read",
    )
    assert model.certificate == VALID_PEM_CERT
    assert model.allowed_scopes == "scope:read"


def test_update_with_invalid_certificate_should_raise() -> None:
    with pytest.raises(ValidationError, match="valid PEM"):
        ClientUpdate(
            common_name="New Name",
            certificate="-----BEGIN CERTIFICATE-----\nnot-valid-base64!!!\n-----END CERTIFICATE-----",
        )


def test_update_missing_common_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        ClientUpdate()  # type: ignore[call-arg]


def test_update_model_dump_exclude_unset_omits_unset_fields() -> None:
    dumped = ClientUpdate(common_name="New Name").model_dump(exclude_unset=True)
    assert dumped == {"common_name": "New Name"}
    assert "certificate" not in dumped
    assert "allowed_scopes" not in dumped


def test_update_model_dump_exclude_unset_includes_explicitly_set_none() -> None:
    dumped = ClientUpdate(common_name="New Name", certificate=None).model_dump(exclude_unset=True)
    assert "certificate" in dumped
    assert dumped["certificate"] is None
