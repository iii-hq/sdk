"""OpenTelemetry initialization for the III Python SDK.

Provides init_otel() / shutdown_otel() which set up distributed tracing
(via EngineSpanExporter), log export (via EngineLogExporter), and
auto-instrument urllib via URLLibInstrumentor.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any

from .telemetry_types import OtelConfig

_tracer: Any = None
_log_provider: Any = None
_connection: Any = None  # SharedEngineConnection | None
_initialized: bool = False
_fetch_patched: bool = False

_DEFAULT_SERVICE_NAME = "iii-python-sdk"


def init_otel(
    config: OtelConfig | None = None,
    loop: asyncio.AbstractEventLoop | None = None,
) -> None:
    """Initialize OpenTelemetry. Subsequent calls are no-ops.

    Args:
        config: OTel configuration.
        loop: Running asyncio event loop. When provided, SharedEngineConnection
              starts immediately. When None, the connection is started lazily
              on first use (pre-start buffer absorbs early frames).
    """
    global _tracer, _log_provider, _connection, _initialized, _fetch_patched

    if _initialized:
        return

    cfg = config or OtelConfig()

    enabled = cfg.enabled
    if enabled is None:
        env = os.environ.get("OTEL_ENABLED", "").lower()
        enabled = env in ("true", "1", "yes", "on")

    if not enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        raise ImportError(
            "opentelemetry-api and opentelemetry-sdk are required. "
            "Install with: pip install 'iii-sdk[otel]'"
        ) from exc

    service_name = (
        cfg.service_name
        or os.environ.get("OTEL_SERVICE_NAME")
        or _DEFAULT_SERVICE_NAME
    )
    service_version = (
        cfg.service_version
        or os.environ.get("SERVICE_VERSION")
        or "unknown"
    )
    service_instance_id = cfg.service_instance_id or str(uuid.uuid4())

    resource_attrs: dict[str, Any] = {
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        "service.instance.id": service_instance_id,
        "telemetry.sdk.name": "iii-python-sdk",
        "telemetry.sdk.language": "python",
    }
    if cfg.service_namespace:
        resource_attrs["service.namespace"] = cfg.service_namespace

    resource = Resource.create(resource_attrs)

    # --- Span exporter ---
    from .telemetry_exporters import EngineSpanExporter, SharedEngineConnection

    ws_url = (
        cfg.engine_ws_url
        or os.environ.get("III_BRIDGE_URL")
        or "ws://localhost:49134"
    )
    _connection = SharedEngineConnection(ws_url)
    if loop is not None:
        _connection.start(loop)

    span_exporter = EngineSpanExporter(_connection)
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("iii-python-sdk")

    # --- Log exporter ---
    logs_enabled = cfg.logs_enabled if cfg.logs_enabled is not None else True
    if logs_enabled:
        _configure_log_provider(resource, _connection)

    _initialized = True

    if cfg.fetch_instrumentation_enabled:
        _enable_fetch_instrumentation()


def _configure_log_provider(resource: Any, connection: Any) -> None:
    """Set up a global SdkLoggerProvider with EngineLogExporter."""
    global _log_provider
    try:
        from opentelemetry import _logs
        from opentelemetry.sdk._logs import LoggerProvider as SdkLoggerProvider
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from .telemetry_exporters import EngineLogExporter
    except ImportError:
        logging.getLogger("iii.telemetry").warning(
            "opentelemetry-sdk logs not available; log export skipped."
        )
        return

    log_exporter = EngineLogExporter(connection)
    log_provider = SdkLoggerProvider(resource=resource)
    log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    _logs.set_logger_provider(log_provider)
    _log_provider = log_provider


def _enable_fetch_instrumentation() -> None:
    """Activate URLLibInstrumentor to auto-patch urllib.request.urlopen."""
    global _fetch_patched
    try:
        from opentelemetry.instrumentation.urllib import URLLibInstrumentor
        URLLibInstrumentor().instrument()
        _fetch_patched = True
    except ImportError:
        logging.getLogger("iii.telemetry").warning(
            "opentelemetry-instrumentation-urllib not installed; "
            "urllib auto-instrumentation skipped. "
            "Install with: pip install 'iii-sdk[otel]'"
        )


def shutdown_otel() -> None:
    """Shut down OTel synchronously (best-effort; does not await WS flush)."""
    _reset_state()


async def shutdown_otel_async() -> None:
    """Shut down OTel and await WebSocket connection close."""
    global _connection
    if _connection is not None:
        await _connection.shutdown()
    _reset_state()


def _reset_state() -> None:
    global _tracer, _log_provider, _connection, _initialized, _fetch_patched

    if _fetch_patched:
        try:
            from opentelemetry.instrumentation.urllib import URLLibInstrumentor
            URLLibInstrumentor().uninstrument()
        except Exception:
            pass
        _fetch_patched = False

    if _initialized:
        try:
            from opentelemetry import trace
            provider = trace.get_tracer_provider()
            if hasattr(provider, "shutdown"):
                provider.shutdown()
        except Exception:
            pass
        try:
            if _log_provider and hasattr(_log_provider, "shutdown"):
                _log_provider.shutdown()
        except Exception:
            pass

    _tracer = None
    _log_provider = None
    _connection = None
    _initialized = False


def get_tracer() -> Any:
    """Return the active tracer, or None if OTel has not been initialized."""
    return _tracer


def is_initialized() -> bool:
    """Return True if OTel has been successfully initialized."""
    return _initialized
