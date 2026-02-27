# iii SDK

Official SDKs for the [iii engine](https://github.com/iii-hq/iii).

[![npm](https://img.shields.io/npm/v/iii-sdk)](https://www.npmjs.com/package/iii-sdk)
[![PyPI](https://img.shields.io/pypi/v/iii-sdk)](https://pypi.org/project/iii-sdk/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

## Packages

| Package | Language | Install | Docs |
|---------|----------|---------|------|
| [`iii-sdk`](https://www.npmjs.com/package/iii-sdk) | Node.js / TypeScript | `npm install iii-sdk` | [README](./packages/node/iii/README.md) |
| [`iii-sdk`](https://pypi.org/project/iii-sdk/) | Python | `pip install iii-sdk` | [README](./packages/python/iii/README.md) |
| [`iii-sdk`](https://crates.io/crates/iii-sdk) | Rust | Add to `Cargo.toml` | [README](./packages/rust/iii/README.md) |

## Quick Start

### Node.js

```javascript
import { init } from 'iii-sdk'

const iii = init('ws://localhost:49134')

iii.registerFunction({ id: 'greet' }, async (input) => {
  return { message: `Hello, ${input.name}!` }
})

const result = await iii.trigger('greet', { name: 'world' })
```

### Python

```python
import asyncio
from iii import III

iii = III("ws://localhost:49134")

async def greet(data):
    return {"message": f"Hello, {data['name']}!"}

iii.register_function("greet", greet)

async def main():
    await iii.connect()
    result = await iii.trigger("greet", {"name": "world"})

asyncio.run(main())
```

### Rust

```rust
use iii_sdk::III;
use serde_json::json;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let iii = III::new("ws://127.0.0.1:49134");
    iii.connect().await?;

    iii.register_function("greet", |input| async move {
        let name = input.get("name").and_then(|v| v.as_str()).unwrap_or("world");
        Ok(json!({ "message": format!("Hello, {name}!") }))
    });

    let result: serde_json::Value = iii
        .trigger("greet", json!({ "name": "world" }))
        .await?;

    Ok(())
}
```

## API Surface

| Operation | Node.js | Python | Rust |
|-----------|---------|--------|------|
| Initialize | `init(url)` | `III(url)` | `III::new(url)` |
| Connect | Auto on `init()` | `await iii.connect()` | `iii.connect().await?` |
| Register function | `iii.registerFunction({ id }, handler)` | `iii.register_function(id, handler)` | `iii.register_function(id, \|input\| ...)` |
| Register trigger | `iii.registerTrigger({ type, function_id, config })` | `iii.register_trigger(type, fn_id, config)` | `iii.register_trigger(type, fn_id, config)?` |
| Invoke (sync) | `await iii.trigger(id, data)` | `await iii.trigger(id, data)` | `iii.trigger(id, data).await?` |
| Invoke (fire-and-forget) | `iii.triggerVoid(id, data)` | `iii.trigger_void(id, data)` | `iii.trigger_void(id, data)?` |

> `call()` and `callVoid()` / `call_void()` exist as deprecated aliases. Use `trigger()` and `triggerVoid()` / `trigger_void()`.

## Development

### Prerequisites

- Node.js 20+ and pnpm (for Node.js SDK)
- Python 3.8+ and uv (for Python SDK)
- Rust 1.70+ and Cargo (for Rust SDK)
- iii engine running on `ws://localhost:49134`

### Building

```bash
cd packages/node && pnpm install && pnpm build
cd packages/python/iii && python -m build
cd packages/rust/iii && cargo build --release
```

### Testing

```bash
cd packages/node && pnpm test
cd packages/python/iii && pytest
cd packages/rust/iii && cargo test
```

## Examples

- [Node.js Example](./packages/node/iii-example/)
- [Python Example](./packages/python/iii-example/)
- [Rust Example](./packages/rust/iii-example/)

## Resources

- [Documentation](https://iii.dev/docs)
- [iii Engine](https://github.com/iii-hq/iii)
- [Examples](https://github.com/iii-hq/iii-examples)

## License

Apache 2.0
