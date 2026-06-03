import pytest
from pydantic import ValidationError

from app.models.oin import Oin
from app.models.organization import OrganizationCreate, OrganizationUpdate

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
    model = OrganizationCreate(oin=Oin("00000099000000001000"), common_name="Test Organization")
    assert str(model.oin) == "00000099000000001000"
    assert model.common_name == "Test Organization"
    assert model.client_certificate is None


def test_create_with_certificate_should_succeed() -> None:
    model = OrganizationCreate(
        oin=Oin("00000099000000001000"),
        common_name="Test Organization",
        client_certificate=VALID_PEM_CERT,
    )
    assert model.client_certificate == VALID_PEM_CERT


def test_create_with_invalid_certificate_should_raise() -> None:
    with pytest.raises(ValidationError, match="valid PEM"):
        OrganizationCreate(
            oin=Oin("00000099000000001000"),
            common_name="Test Organization",
            client_certificate="-----BEGIN CERTIFICATE-----\nnot-valid-base64!!!\n-----END CERTIFICATE-----",
        )


def test_create_with_garbage_certificate_should_raise() -> None:
    with pytest.raises(ValidationError, match="valid PEM"):
        OrganizationCreate(
            oin=Oin("00000099000000001000"),
            common_name="Test Organization",
            client_certificate="this is not a certificate at all",
        )


def test_create_missing_oin_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(common_name="Test Organization")  # type: ignore[call-arg]


def test_create_missing_common_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(oin=Oin("00000099000000001000"))  # type: ignore[call-arg]


def test_update_should_succeed() -> None:
    model = OrganizationUpdate(common_name="New Name")
    assert model.common_name == "New Name"
    assert model.client_certificate is None


def test_update_with_valid_certificate_should_succeed() -> None:
    model = OrganizationUpdate(common_name="New Name", client_certificate=VALID_PEM_CERT)
    assert model.client_certificate == VALID_PEM_CERT


def test_update_with_invalid_certificate_should_raise() -> None:
    with pytest.raises(ValidationError, match="valid PEM"):
        OrganizationUpdate(
            common_name="New Name",
            client_certificate="not-a-pem",
        )


def test_update_missing_common_name_should_raise() -> None:
    with pytest.raises(ValidationError):
        OrganizationUpdate()  # type: ignore[call-arg]
