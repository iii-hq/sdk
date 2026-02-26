"""Streaming channel writer and reader backed by WebSocket connections."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable
from urllib.parse import quote

import websockets
from websockets.asyncio.client import ClientConnection

from .iii_types import StreamChannelRef

log = logging.getLogger("iii.channels")


def build_channel_url(
    engine_ws_base: str,
    channel_id: str,
    access_key: str,
    direction: str,
) -> str:
    base = engine_ws_base.rstrip("/")
    return f"{base}/ws/channels/{channel_id}?key={quote(access_key)}&dir={direction}"


class ChannelWriter:
    """WebSocket-backed writer for streaming binary data and text messages."""

    def __init__(self, engine_ws_base: str, ref: StreamChannelRef) -> None:
        self._url = build_channel_url(engine_ws_base, ref.channel_id, ref.access_key, "write")
        self._ws: ClientConnection | None = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def _ensure_connected(self) -> ClientConnection:
        if self._ws is not None and self._connected:
            return self._ws
        async with self._lock:
            if self._ws is not None and self._connected:
                return self._ws
            self._ws = await websockets.connect(self._url)
            self._connected = True
            return self._ws

    _MAX_FRAME_SIZE = 64 * 1024

    async def write(self, data: bytes) -> None:
        ws = await self._ensure_connected()
        if len(data) <= self._MAX_FRAME_SIZE:
            await ws.send(data)
        else:
            offset = 0
            while offset < len(data):
                await ws.send(data[offset:offset + self._MAX_FRAME_SIZE])
                offset += self._MAX_FRAME_SIZE

    def send_message(self, msg: str) -> None:
        """Fire-and-forget text message. Queues a coroutine on the running loop."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._send_message_async(msg))
        except RuntimeError:
            asyncio.run(self._send_message_async(msg))

    async def _send_message_async(self, msg: str) -> None:
        ws = await self._ensure_connected()
        await ws.send(msg)

    async def send_message_async(self, msg: str) -> None:
        ws = await self._ensure_connected()
        await ws.send(msg)

    def close(self) -> None:
        """Fire-and-forget close."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.close_async())
        except RuntimeError:
            asyncio.run(self.close_async())

    async def close_async(self) -> None:
        if self._ws is not None and self._connected:
            await self._ws.close()
            self._connected = False


class ChannelReader:
    """WebSocket-backed reader for streaming binary data and text messages."""

    def __init__(self, engine_ws_base: str, ref: StreamChannelRef) -> None:
        self._url = build_channel_url(engine_ws_base, ref.channel_id, ref.access_key, "read")
        self._ws: ClientConnection | None = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._message_callbacks: list[Callable[[str], Any]] = []

    async def _ensure_connected(self) -> ClientConnection:
        if self._ws is not None and self._connected:
            return self._ws
        async with self._lock:
            if self._ws is not None and self._connected:
                return self._ws
            self._ws = await websockets.connect(self._url)
            self._connected = True
            return self._ws

    def on_message(self, callback: Callable[[str], Any]) -> None:
        self._message_callbacks.append(callback)

    async def __aiter__(self):
        """Async iterator that yields binary chunks and dispatches text messages to callbacks."""
        ws = await self._ensure_connected()
        try:
            async for message in ws:
                if isinstance(message, bytes):
                    yield message
                else:
                    for cb in self._message_callbacks:
                        try:
                            cb(message)
                        except Exception:
                            log.exception("Error in channel message callback")
        except websockets.ConnectionClosed:
            pass

    async def read_all(self) -> bytes:
        """Read the entire stream into a single bytes object."""
        chunks: list[bytes] = []
        async for chunk in self:
            chunks.append(chunk)
        return b"".join(chunks)

    async def close_async(self) -> None:
        if self._ws is not None and self._connected:
            await self._ws.close()
            self._connected = False
