"""Tests for OtelConfig dataclass."""
from iii.telemetry_types import OtelConfig


def test_otel_config_defaults():
    config = OtelConfig()
    assert config.enabled is None
    assert config.service_name is None
    assert config.engine_ws_url is None
    assert config.fetch_instrumentation_enabled is True


def test_otel_config_explicit_values():
    config = OtelConfig(
        enabled=True,
        service_name="my-service",
        engine_ws_url="ws://localhost:49134",
        fetch_instrumentation_enabled=False,
    )
    assert config.enabled is True
    assert config.service_name == "my-service"
    assert config.fetch_instrumentation_enabled is False


def test_otel_config_has_otlp_endpoint_field():
    from iii.telemetry_types import OtelConfig
    cfg = OtelConfig(otlp_endpoint="http://localhost:4318")
    assert cfg.otlp_endpoint == "http://localhost:4318"


def test_otel_config_otlp_endpoint_defaults_to_none():
    from iii.telemetry_types import OtelConfig
    cfg = OtelConfig()
    assert cfg.otlp_endpoint is None
