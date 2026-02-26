"""Tests for HTTP external functions. Unit tests use FakeWebSocket; integration test requires running III engine with HttpFunctionsModule."""

import asyncio
import json
import os
import random
import time
from typing import Any

import pytest

from iii import III, HttpInvocationConfig, InitOptions


def _unique_function_id(prefix: str) -> str:
    return f"{prefix}::{int(time.time())}::{random.random():.10f}".replace(".", "")


def _unique_topic(prefix: str) -> str:
    return f"{prefix}.{int(time.time())}.{random.random():.10f}".replace(".", "")


class WebhookProbe:
    def __init__(self) -> None:
        self._received: list[dict[str, Any]] = []
        self._waiter: asyncio.Future[dict[str, Any]] | None = None
        self._server: asyncio.Server | None = None
        self._port = 0

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_request,
            "127.0.0.1",
            0,
        )
        for sock in self._server.sockets or []:
            self._port = sock.getsockname()[1]
            break

    async def _handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        data = b""
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break
            data += chunk
            if b"\r\n\r\n" in data or b"\n\n" in data:
                break

        lines = data.decode().split("\r\n") if data else []
        method = "POST"
        if lines:
            parts = lines[0].split()
            if len(parts) >= 1:
                method = parts[0]
        path = "/"
        if lines and " " in lines[0]:
            path = lines[0].split(" ")[1].split("?")[0]

        body = b""
        if b"\r\n\r\n" in data:
            body = data.split(b"\r\n\r\n", 1)[1]
        elif b"\n\n" in data:
            body = data.split(b"\n\n", 1)[1]

        try:
            body_json = json.loads(body.decode()) if body else None
        except Exception:
            body_json = body.decode() if body else None

        captured = {"method": method, "url": path, "body": body_json}
        self._received.append(captured)
        if self._waiter and not self._waiter.done():
            self._waiter.set_result(captured)

        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
        writer.write(b'{"ok":true}')
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def close(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    def url(self, path: str = "/webhook") -> str:
        return f"http://127.0.0.1:{self._port}{path}"

    async def wait_for_webhook(self, timeout: float = 7.0) -> dict[str, Any]:
        if self._received:
            return self._received.pop(0)
        self._waiter = asyncio.get_running_loop().create_future()
        try:
            return await asyncio.wait_for(self._waiter, timeout=timeout)
        finally:
            self._waiter = None


@pytest.mark.asyncio
async def test_register_http_function_sends_invocation_message(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    import iii.iii as iii_module

    sent: list[dict] = []

    class FakeWs:
        state = SimpleNamespace(name="OPEN")

        async def send(self, payload: str) -> None:
            sent.append(__import__("json").loads(payload))

        async def close(self) -> None:
            self.state = SimpleNamespace(name="CLOSED")

        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    async def fake_connect(_: str) -> FakeWs:
        return FakeWs()

    monkeypatch.setattr(iii_module.websockets, "connect", fake_connect)

    client = III("ws://fake", InitOptions())
    client._register_worker_metadata = lambda: None

    await client.connect()
    await asyncio.sleep(0.01)

    config = HttpInvocationConfig(url="https://example.com/invoke", method="POST", timeout_ms=3000)
    ref = client.register_http_function("external::my_lambda", config)
    await asyncio.sleep(0.02)

    assert ref.id == "external::my_lambda"
    reg_fn = [m for m in sent if m.get("type") == "registerfunction" and m.get("id") == "external::my_lambda"]
    assert len(reg_fn) == 1
    assert reg_fn[0].get("invocation", {}).get("url") == "https://example.com/invoke"
    assert reg_fn[0].get("invocation", {}).get("method") == "POST"

    ref.unregister()
    await asyncio.sleep(0.05)
    unreg = [m for m in sent if m.get("type") == "unregisterfunction" and m.get("id") == "external::my_lambda"]
    assert len(unreg) == 1, f"Expected 1 unregister message, got {len(unreg)}. Sent: {sent}"

    await client.shutdown()


@pytest.mark.asyncio
async def test_delivers_queue_events_to_external_http_function() -> None:
    ws_url = os.environ.get("III_BRIDGE_URL", "ws://localhost:49199")
    client = III(ws_url, InitOptions(reconnection_config=None))
    client._register_worker_metadata = lambda: None

    await client.connect()
    await asyncio.sleep(0.1)

    try:
        _ = await client.trigger("engine::functions::list", {})
    except Exception:
        pytest.skip("III engine not available")

    probe = WebhookProbe()
    await probe.start()

    function_id = _unique_function_id("test::http_external::target")
    topic = _unique_topic("test.http_external.topic")
    payload = {"hello": "world", "count": 1}
    trigger = None
    http_fn = None

    try:
        http_fn = client.register_http_function(
            function_id,
            HttpInvocationConfig(url=probe.url(), method="POST", timeout_ms=3000),
        )
        await asyncio.sleep(0.3)

        trigger = client.register_trigger("queue", function_id, {"topic": topic})
        await asyncio.sleep(0.3)

        await client.trigger("enqueue", {"topic": topic, "data": payload})

        webhook = await probe.wait_for_webhook(7.0)

        assert webhook["method"] == "POST"
        assert webhook["url"] == "/webhook"
        assert webhook["body"] == payload
    finally:
        if trigger:
            trigger.unregister()
        if http_fn:
            http_fn.unregister()
        await probe.close()
        await client.shutdown()
