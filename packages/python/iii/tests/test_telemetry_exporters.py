"""Tests for SharedEngineConnection, EngineSpanExporter, EngineLogExporter."""
import asyncio
import pytest

from iii.telemetry_exporters import SharedEngineConnection


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def test_send_threadsafe_before_start_buffers_frame():
    """Frames sent before start() are buffered in pre-start deque."""
    conn = SharedEngineConnection("ws://localhost:99999")  # unreachable
    conn.send_threadsafe(b"OTLP", b"hello")
    assert len(conn._pre_start_buffer) == 1
    prefix, payload = conn._pre_start_buffer[0]
    assert prefix == b"OTLP"
    assert payload == b"hello"


def test_pre_start_buffer_drops_oldest_when_full():
    """Pre-start buffer drops oldest frame when MAX_QUEUE exceeded."""
    conn = SharedEngineConnection("ws://localhost:99999")
    for i in range(SharedEngineConnection.MAX_QUEUE + 1):
        conn.send_threadsafe(b"OTLP", str(i).encode())
    assert len(conn._pre_start_buffer) == SharedEngineConnection.MAX_QUEUE
    # Oldest (0) was dropped; newest is still present
    _, last = conn._pre_start_buffer[-1]
    assert last == str(SharedEngineConnection.MAX_QUEUE).encode()


@pytest.mark.asyncio
async def test_start_drains_pre_start_buffer_into_queue():
    """start() moves buffered frames into the asyncio queue."""
    conn = SharedEngineConnection("ws://localhost:99999")
    conn.send_threadsafe(b"OTLP", b"span1")
    conn.send_threadsafe(b"LOGS", b"log1")

    loop = asyncio.get_event_loop()
    # Patch _run to be a no-op so we don't attempt real connection
    async def _noop():
        await asyncio.sleep(9999)
    conn._run = _noop

    conn.start(loop)
    assert conn._queue is not None
    assert conn._queue.qsize() == 2
    assert len(conn._pre_start_buffer) == 0
    await conn.shutdown()
