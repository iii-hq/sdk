"""III SDK for Python."""

import logging

from .context import Context, get_context, with_context
from .iii import III, ConnectionStateCallback, FunctionRef, IIIConnectionState, InitOptions, ReconnectionConfig
from .iii_types import FunctionInfo, WorkerInfo, WorkerStatus
from .logger import Logger
from .stream import (
    IStream,
    StreamAuthInput,
    StreamAuthResult,
    StreamDeleteInput,
    StreamGetInput,
    StreamJoinLeaveEvent,
    StreamJoinResult,
    StreamListGroupsInput,
    StreamListInput,
    StreamSetInput,
    StreamSetResult,
    StreamUpdateInput,
    UpdateDecrement,
    UpdateIncrement,
    UpdateMerge,
    UpdateOp,
    UpdateRemove,
    UpdateSet,
)
from .types import ApiRequest, ApiResponse, FunctionsAvailableCallback, RemoteFunctionHandler
from .telemetry import get_meter, get_tracer, init_otel, is_initialized, shutdown_otel
from .telemetry_types import OtelConfig


def configure_logging(level: int = logging.INFO, format: str | None = None) -> None:
    """Configure logging for the III SDK.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        format: Log format string. Defaults to a simple format.
    """
    if format is None:
        format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    logging.basicConfig(level=level, format=format)
    logging.getLogger("iii").setLevel(level)


__all__ = [
    # Core
    "III",
    "InitOptions",
    "ReconnectionConfig",
    "IIIConnectionState",
    "ConnectionStateCallback",
    "FunctionRef",
    "Logger",
    "Context",
    "get_context",
    "with_context",
    # API types
    "ApiRequest",
    "ApiResponse",
    # SDK types
    "FunctionInfo",
    "WorkerInfo",
    "WorkerStatus",
    # Stream types
    "IStream",
    "StreamAuthInput",
    "StreamAuthResult",
    "StreamDeleteInput",
    "StreamListInput",
    "StreamGetInput",
    "StreamJoinLeaveEvent",
    "StreamJoinResult",
    "StreamListGroupsInput",
    "StreamSetInput",
    "StreamSetResult",
    "StreamUpdateInput",
    "UpdateDecrement",
    "UpdateIncrement",
    "UpdateMerge",
    "UpdateOp",
    "UpdateRemove",
    "UpdateSet",
    # Callbacks
    "FunctionsAvailableCallback",
    "RemoteFunctionHandler",
    # Telemetry
    "OtelConfig",
    "init_otel",
    "shutdown_otel",
    "get_tracer",
    "get_meter",
    "is_initialized",
    # Utility
    "configure_logging",
]
