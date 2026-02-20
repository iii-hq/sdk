"""Tests for OTel-bridge behavior of Logger."""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def reset_otel():
    from iii.telemetry import shutdown_otel
    yield
    shutdown_otel()
    # Reset all OTel global singletons so tests don't bleed state
    try:
        import opentelemetry._logs._internal as _li
        _li._LOGGER_PROVIDER = None
        _li._LOGGER_PROVIDER_SET_ONCE._done = False
    except Exception:
        pass
    try:
        import opentelemetry.trace._internal as _ti
        _ti._TRACER_PROVIDER = None
        _ti._TRACER_PROVIDER_SET_ONCE._done = False
    except Exception:
        pass
    try:
        import opentelemetry.metrics._internal as _mi
        _mi._METER_PROVIDER = None
        _mi._METER_PROVIDER_SET_ONCE._done = False
    except Exception:
        pass


def _setup_in_memory_log_provider():
    from opentelemetry.sdk._logs import LoggerProvider as SdkLoggerProvider
    from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
    from opentelemetry import _logs

    log_exporter = InMemoryLogRecordExporter()
    lp = SdkLoggerProvider()
    lp.add_log_record_processor(SimpleLogRecordProcessor(log_exporter))
    _logs.set_logger_provider(lp)
    return log_exporter


def test_logger_emits_otel_record_when_initialized():
    """Logger.info emits an OTel LogRecord with severity INFO when OTel is active."""
    from iii.telemetry import init_otel
    from iii.telemetry_types import OtelConfig
    from iii.logger import Logger

    log_exporter = _setup_in_memory_log_provider()
    init_otel(OtelConfig(enabled=True, logs_enabled=False))  # skip EngineLogExporter

    logger = Logger(trace_id="t1", function_name="fn1")
    logger.info("hello world", {"key": "val"})

    records = log_exporter.get_finished_logs()
    assert len(records) == 1
    assert records[0].log_record.body == "hello world"
    assert records[0].log_record.severity_text == "INFO"


def test_logger_emits_warn_severity():
    from iii.logger import Logger
    from opentelemetry._logs import SeverityNumber

    log_exporter = _setup_in_memory_log_provider()

    with patch("iii.logger.is_initialized", return_value=True):
        logger = Logger()
        logger.warn("watch out")

    records = log_exporter.get_finished_logs()
    assert len(records) == 1
    assert records[0].log_record.severity_number == SeverityNumber.WARN


def test_logger_falls_back_to_invoker_when_otel_not_initialized():
    """Logger.info calls invoker with engine::log::info when OTel not initialized."""
    from iii.logger import Logger

    invoker = MagicMock()
    logger = Logger(invoker=invoker, trace_id="t1", function_name="fn1")
    logger.info("test message")

    invoker.assert_called_once_with("engine::log::info", {
        "message": "test message",
        "trace_id": "t1",
        "function_name": "fn1",
        "data": None,
    })


def test_logger_does_not_call_invoker_when_otel_initialized():
    """Logger.info does NOT call engine::log::info when OTel is active."""
    from iii.logger import Logger

    _setup_in_memory_log_provider()
    invoker = MagicMock()

    with patch("iii.logger.is_initialized", return_value=True):
        logger = Logger(invoker=invoker)
        logger.info("otel message")

    invoker.assert_not_called()
