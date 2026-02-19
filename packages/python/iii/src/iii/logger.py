"""Logger implementation for the III SDK."""
from __future__ import annotations

import logging
import time
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

log = logging.getLogger("iii.logger")


class LoggerParams(BaseModel):
    """Parameters for logger invocation."""

    model_config = ConfigDict(populate_by_name=True)

    message: str
    trace_id: str = Field(default="", serialization_alias="trace_id")
    function_name: str = Field(default="", serialization_alias="function_name")
    data: Any = None


LoggerInvoker = Callable[[str, dict[str, Any]], None]

_SEVERITY_MAP = {
    "info": ("INFO", 9),    # SeverityNumber.INFO
    "warn": ("WARN", 13),   # SeverityNumber.WARN
    "error": ("ERROR", 17), # SeverityNumber.ERROR
    "debug": ("DEBUG", 5),  # SeverityNumber.DEBUG
}


def is_initialized() -> bool:
    """Return True if OTel has been initialized (importable without circular dep)."""
    try:
        from .telemetry import is_initialized as _is_init
        return _is_init()
    except ImportError:
        return False


class Logger:
    """Logger that emits OTel LogRecords when OTel is active, otherwise
    sends log messages through the III engine via WebSocket function calls."""

    def __init__(
        self,
        invoker: LoggerInvoker | None = None,
        trace_id: str | None = None,
        function_name: str | None = None,
    ) -> None:
        self._invoker = invoker
        self._trace_id = trace_id or ""
        self._function_name = function_name or ""

    def _build_params(self, message: str, data: Any = None) -> dict[str, Any]:
        return {
            "message": message,
            "trace_id": self._trace_id,
            "function_name": self._function_name,
            "data": data,
        }

    def _emit_otel(self, level: str, message: str, data: Any = None) -> bool:
        """Emit an OTel LogRecord. Returns True if emitted, False if OTel not active."""
        if not is_initialized():
            return False
        try:
            from opentelemetry import _logs
            from opentelemetry._logs import SeverityNumber
            from opentelemetry._logs import LogRecord

            severity_text, severity_num = _SEVERITY_MAP[level]
            otel_logger = _logs.get_logger("iii.logger")
            attrs: dict[str, Any] = {"function_name": self._function_name}
            if self._trace_id:
                attrs["trace_id"] = self._trace_id
            if data is not None:
                attrs["data"] = str(data)

            record = LogRecord(
                timestamp=time.time_ns(),
                observed_timestamp=time.time_ns(),
                severity_text=severity_text,
                severity_number=SeverityNumber(severity_num),
                body=message,
                attributes=attrs,
            )
            otel_logger.emit(record)
            return True
        except Exception:
            return False

    def info(self, message: str, data: Any = None) -> None:
        if not self._emit_otel("info", message, data):
            if self._invoker:
                self._invoker("engine::log::info", self._build_params(message, data))
        log.info("[%s] %s", self._function_name, message, extra={"data": data})

    def warn(self, message: str, data: Any = None) -> None:
        if not self._emit_otel("warn", message, data):
            if self._invoker:
                self._invoker("engine::log::warn", self._build_params(message, data))
        log.warning("[%s] %s", self._function_name, message, extra={"data": data})

    def error(self, message: str, data: Any = None) -> None:
        if not self._emit_otel("error", message, data):
            if self._invoker:
                self._invoker("engine::log::error", self._build_params(message, data))
        log.error("[%s] %s", self._function_name, message, extra={"data": data})

    def debug(self, message: str, data: Any = None) -> None:
        if not self._emit_otel("debug", message, data):
            if self._invoker:
                self._invoker("engine::log::debug", self._build_params(message, data))
        log.debug("[%s] %s", self._function_name, message, extra={"data": data})
