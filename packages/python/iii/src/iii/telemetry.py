"""
OpenTelemetry initialization for the III Python SDK.

Provides init_otel() / shutdown_otel() which set up distributed tracing
and auto-instrument urllib via the official URLLibInstrumentor.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

from .telemetry_types import OtelConfig

_tracer: Any = None
_initialized: bool = False
_fetch_patched: bool = False

_DEFAULT_SERVICE_NAME = "iii-python-sdk"


def init_otel(config: OtelConfig | None = None) -> None:
    """Initialize OpenTelemetry. Subsequent calls are no-ops.

    Requires opentelemetry-api, opentelemetry-sdk, and
    opentelemetry-instrumentation-urllib to be installed.
    Install with: pip install 'iii-sdk[otel]'
    """
    global _tracer, _initialized, _fetch_patched

    if _initialized:
        return

    cfg = config or OtelConfig()

    # Resolve enabled flag (env var OTEL_ENABLED overrides if config.enabled is None)
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
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    _configure_otlp_exporter(provider, cfg)

    _tracer = trace.get_tracer("iii-python-sdk")
    _initialized = True

    if cfg.fetch_instrumentation_enabled:
        _enable_fetch_instrumentation()


def _configure_otlp_exporter(provider: Any, cfg: "OtelConfig") -> None:
    """Attach an OTLP HTTP span exporter to the TracerProvider."""
    try:
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    except ImportError:
        import logging
        logging.getLogger("iii.telemetry").warning(
            "opentelemetry-exporter-otlp-proto-http not installed; "
            "span export skipped. Install with: pip install 'iii-sdk[otel]'"
        )
        return

    endpoint = (
        cfg.otlp_endpoint
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        or "http://localhost:4318"
    )
    exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))


def _enable_fetch_instrumentation() -> None:
    """Activate URLLibInstrumentor to auto-patch urllib.request.urlopen."""
    global _fetch_patched
    try:
        from opentelemetry.instrumentation.urllib import URLLibInstrumentor
        URLLibInstrumentor().instrument()
        _fetch_patched = True
    except ImportError:
        import logging
        logging.getLogger("iii.telemetry").warning(
            "opentelemetry-instrumentation-urllib not installed; "
            "urllib auto-instrumentation skipped. "
            "Install with: pip install 'iii-sdk[otel]'"
        )


def shutdown_otel() -> None:
    """Shut down OTel and restore urllib to its original state."""
    global _tracer, _initialized, _fetch_patched

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

    _tracer = None
    _initialized = False


def get_tracer() -> Any:
    """Return the active tracer, or None if OTel has not been initialized."""
    return _tracer


def is_initialized() -> bool:
    """Return True if OTel has been successfully initialized."""
    return _initialized
