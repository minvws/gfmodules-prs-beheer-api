from pydantic import SecretStr

from app.config import Config, ConfigApp, ConfigDatabase, ConfigStats, ConfigTelemetry, ConfigUvicorn


def get_test_config() -> Config:
    return Config(
        app=ConfigApp(),
        database=ConfigDatabase(dsn=SecretStr("sqlite:///:memory:")),
        telemetry=ConfigTelemetry(),
        stats=ConfigStats(),
        uvicorn=ConfigUvicorn(),
    )
