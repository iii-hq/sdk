import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest

import iii.bridge as bridge_module
from iii import III


class FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []
        self.state = SimpleNamespace(name="OPEN")

    async def send(self, payload: str) -> None:
        self.sent.append(json.loads(payload))

    async def close(self) -> None:
        self.state = SimpleNamespace(name="CLOSED")

    def __aiter__(self) -> "FakeWebSocket":
        return self

    async def __anext__(self) -> Any:
        raise StopAsyncIteration


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_preconnect_registration_sent_once(monkeypatch: pytest.MonkeyPatch) -> None:
    ws = FakeWebSocket()
    connect_calls = 0

    async def fake_connect(_addr: str) -> FakeWebSocket:
        nonlocal connect_calls
        connect_calls += 1
        return ws

    monkeypatch.setattr(bridge_module.websockets, "connect", fake_connect)

    client = III("ws://fake")
    client._register_worker_metadata = lambda: None

    async def handler(data: Any) -> Any:
        return data

    client.register_function("demo.fn", handler)
    client.register_trigger("cron", "demo.fn", {"cron": "* * * * * *"})

    assert client._queue == []

    await client.connect()
    await asyncio.sleep(0.01)
    await client.shutdown()

    reg_fn = [m for m in ws.sent if m.get("type") == "registerfunction" and m.get("id") == "demo.fn"]
    reg_trigger = [m for m in ws.sent if m.get("type") == "registertrigger" and m.get("function_id") == "demo.fn"]

    assert connect_calls == 1
    assert len(reg_fn) == 1, ws.sent
    assert len(reg_trigger) == 1, ws.sent


@pytest.mark.anyio
async def test_reconnect_replays_durable_state_once_per_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sockets: list[FakeWebSocket] = []

    async def fake_connect(_addr: str) -> FakeWebSocket:
        ws = FakeWebSocket()
        sockets.append(ws)
        return ws

    monkeypatch.setattr(bridge_module.websockets, "connect", fake_connect)

    client = III("ws://fake")
    client._register_worker_metadata = lambda: None

    async def handler(data: Any) -> Any:
        return data

    client.register_function("demo.fn", handler)
    client.register_trigger("cron", "demo.fn", {"cron": "* * * * * *"})

    await client.connect()
    await asyncio.sleep(0.01)

    first_ws = client._ws
    assert first_ws is not None
    await first_ws.close()
    client._ws = None

    await client._do_connect()
    await asyncio.sleep(0.01)
    await client.shutdown()

    total_fn = sum(
        1 for ws in sockets for m in ws.sent if m.get("type") == "registerfunction" and m.get("id") == "demo.fn"
    )
    total_trigger = sum(
        1 for ws in sockets for m in ws.sent if m.get("type") == "registertrigger" and m.get("function_id") == "demo.fn"
    )

    assert total_fn == 2
    assert total_trigger == 2


@pytest.mark.anyio
async def test_call_void_queued_while_disconnected_flushes_after_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ws = FakeWebSocket()

    async def fake_connect(_addr: str) -> FakeWebSocket:
        return ws

    monkeypatch.setattr(bridge_module.websockets, "connect", fake_connect)

    client = III("ws://fake")
    client._register_worker_metadata = lambda: None

    client.call_void("demo.fire", {"x": 1})
    await asyncio.sleep(0)

    await client.connect()
    await asyncio.sleep(0.01)
    await client.shutdown()

    invoke = [m for m in ws.sent if m.get("type") == "invokefunction" and m.get("function_id") == "demo.fire"]
    assert len(invoke) == 1
