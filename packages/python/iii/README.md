# iii-sdk

Python SDK for the [iii engine](https://github.com/iii-hq/iii).

[![PyPI](https://img.shields.io/pypi/v/iii-sdk)](https://pypi.org/project/iii-sdk/)
[![Python](https://img.shields.io/pypi/pyversions/iii-sdk)](https://pypi.org/project/iii-sdk/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](../../../LICENSE)

## Install

```bash
pip install iii-sdk
```

## Quick Start

```python
import asyncio
from iii import III

iii = III("ws://localhost:49134")

async def greet(data):
    return {"message": f"Hello, {data['name']}!"}

iii.register_function("greet", greet)

async def main():
    await iii.connect()

    iii.register_trigger(
        type="http",
        function_id="greet",
        config={"api_path": "greet", "http_method": "POST"}
    )

    result = await iii.trigger("greet", {"name": "world"})
    print(result)

asyncio.run(main())
```

## API

| Method | Description |
|--------|-------------|
| `III(url)` | Create an SDK instance |
| `await iii.connect()` | Connect to the engine (sets up WebSocket + OTel) |
| `iii.register_function(id, handler)` | Register a callable function |
| `iii.register_trigger(type, function_id, config)` | Bind a trigger to a function |
| `await iii.trigger(id, data)` | Invoke a function and wait for the result |
| `iii.trigger_void(id, data)` | Invoke a function without waiting (fire-and-forget) |

### Connection

Python requires an explicit `await iii.connect()` call (no async constructors in Python). This sets up both the WebSocket connection and OpenTelemetry instrumentation.

### HTTP Trigger Example

```python
from iii import III, ApiRequest, ApiResponse

iii = III("ws://localhost:49134")

async def create_todo(data):
    req = ApiRequest(**data)
    return ApiResponse(status=201, data={"id": "123", "title": req.body.get("title")})

iii.register_function("api.post.todo", create_todo)

async def main():
    await iii.connect()

    iii.register_trigger(
        type="http",
        function_id="api.post.todo",
        config={
            "api_path": "todo",
            "http_method": "POST",
            "description": "Create a new todo"
        }
    )
```

## Deprecated

`call()` and `call_void()` are deprecated aliases for `trigger()` and `trigger_void()`. They still work but will be removed in a future release.

## Resources

- [Documentation](https://iii.dev/docs)
- [iii Engine](https://github.com/iii-hq/iii)
- [Examples](https://github.com/iii-hq/iii-examples)
