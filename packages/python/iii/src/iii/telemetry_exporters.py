"""WebSocket-based OTel exporters for the III Engine.

Spans → binary WS frame: b"OTLP" + OTLP JSON bytes
Logs  → binary WS frame: b"LOGS" + OTLP JSON bytes
"""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    pass

log = logging.getLogger("iii.telemetry_exporters")


class SharedEngineConnection:
    """Dedicated asyncio WebSocket connection for OTel telemetry data.

    Thread-safe: send_threadsafe() may be called from any thread (e.g. the
    OTel BatchSpanProcessor background thread). Frames sent before start()
    are buffered and flushed once the connection is established.
    """

    MAX_QUEUE: int = 1000

    def __init__(self, url: str) -> None:
        self._url = url
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None  # type: ignore[type-arg]
        self._queue: asyncio.Queue | None = None  # type: ignore[type-arg]
        self._pre_start_buffer: deque[tuple[bytes, bytes]] = deque(maxlen=self.MAX_QUEUE)
        self._started = False

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start the connection on the given event loop. Call once after connect()."""
        self._loop = loop
        self._queue = asyncio.Queue()
        # Drain pre-start buffer into asyncio queue
        while self._pre_start_buffer:
            self._queue.put_nowait(self._pre_start_buffer.popleft())
        self._task = loop.create_task(self._run())
        self._started = True

    def send_threadsafe(self, prefix: bytes, payload: bytes) -> None:
        """Enqueue a binary frame from any thread.

        If called before start(), frames are buffered in _pre_start_buffer.
        """
        if not self._started or self._loop is None or self._queue is None:
            self._pre_start_buffer.append((prefix, payload))
            return
        asyncio.run_coroutine_threadsafe(
            self._queue.put((prefix, payload)), self._loop
        )

    async def _run(self) -> None:
        """Main reconnect loop — runs as an asyncio Task."""
        import websockets  # noqa: PLC0415

        delay = 1.0
        while True:
            try:
                async with websockets.connect(self._url) as ws:
                    log.debug("OTel WS connected to %s", self._url)
                    delay = 1.0
                    while True:
                        assert self._queue is not None
                        prefix, payload = await self._queue.get()
                        await ws.send(prefix + payload)
            except asyncio.CancelledError:
                return
            except Exception as exc:
                log.warning("OTel WS disconnected (%s), retrying in %.1fs", exc, delay)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30.0)

    async def shutdown(self) -> None:
        """Cancel the connection task."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


def _serialize_spans(spans: Sequence) -> bytes:
    """Serialize ReadableSpans to OTLP JSON bytes."""
    from opentelemetry.exporter.otlp.proto.common._internal.trace_encoder import encode_spans
    from google.protobuf.json_format import MessageToJson

    proto = encode_spans(spans)  # type: ignore[arg-type]
    return MessageToJson(proto).encode()


def _serialize_logs(batch: Sequence) -> bytes:
    """Serialize ReadableLogRecord objects to OTLP JSON bytes."""
    from opentelemetry.exporter.otlp.proto.common._internal._log_encoder import encode_logs
    from google.protobuf.json_format import MessageToJson

    proto = encode_logs(batch)  # type: ignore[arg-type]
    return MessageToJson(proto).encode()


class EngineSpanExporter:
    """SpanExporter that sends OTLP JSON over the engine WebSocket connection."""

    def __init__(self, connection: SharedEngineConnection) -> None:
        self._connection = connection

    def export(self, spans: Sequence) -> "SpanExportResult":
        from opentelemetry.sdk.trace.export import SpanExportResult

        try:
            json_bytes = _serialize_spans(spans)
            self._connection.send_threadsafe(b"OTLP", json_bytes)
            return SpanExportResult.SUCCESS
        except Exception:
            log.exception("EngineSpanExporter.export failed")
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True


class EngineLogExporter:
    """LogExporter that sends OTLP JSON over the engine WebSocket connection."""

    def __init__(self, connection: SharedEngineConnection) -> None:
        self._connection = connection

    def export(self, batch: Sequence) -> "LogExportResult":
        from opentelemetry.sdk._logs.export import LogExportResult

        try:
            json_bytes = _serialize_logs(batch)
            self._connection.send_threadsafe(b"LOGS", json_bytes)
            return LogExportResult.SUCCESS
        except Exception:
            log.exception("EngineLogExporter.export failed")
            return LogExportResult.FAILURE

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True
