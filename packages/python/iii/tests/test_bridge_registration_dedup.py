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

    async def fake_connect(_addr: str) -> FakeWebSocket:
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
    await client.shutdown()

    reg_fn = [m for m in ws.sent if m.get("type") == "registerfunction" and m.get("id") == "demo.fn"]
    reg_trigger = [m for m in ws.sent if m.get("type") == "registertrigger" and m.get("function_id") == "demo.fn"]

    assert len(reg_fn) == 1
    assert len(reg_trigger) == 1
