# III SDK for Python

Python SDK for the III Engine.

## Installation

```bash
pip install iii-sdk
```

## Usage

```python
from iii import III, Logger

# Create an III SDK instance
iii = III("ws://localhost:8080")

# Register a function
@iii.function("my.function")
async def my_function(data):
    return {"result": "success"}

# Invoke a function
result = await iii.call("other.function", {"param": "value"})
```

### Build & Publish
```bash
python -m build
uv publish --index cloudsmith dist/*
```

## Features

- WebSocket-based communication with III Engine
- Function registration and invocation
- Trigger registration
- Context-aware logging
- Async/await support
