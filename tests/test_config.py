from pydantic import SecretStr

from app.config import (
    Config,
    ConfigApp,
    ConfigDatabase,
    ConfigLogging,
    ConfigStats,
    ConfigTelemetry,
    ConfigUvicorn,
    read_ini_file,
)


def get_test_config() -> Config:
    return Config(
        app=ConfigApp(),
        database=ConfigDatabase(dsn=SecretStr("sqlite:///:memory:")),
        telemetry=ConfigTelemetry(),
        stats=ConfigStats(),
        uvicorn=ConfigUvicorn(),
    )


def test_the_example_config_reads_the_logging_streams() -> None:
    logging = ConfigLogging.model_validate(read_ini_file("app.conf.example")["logging"])

    assert logging.syslog_streams == ["app", "siem", "public_inspect"]
    assert logging.console_streams == ["debug"]
