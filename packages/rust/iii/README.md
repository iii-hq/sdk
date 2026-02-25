# iii-sdk

Rust SDK for the [iii engine](https://github.com/iii-hq/iii).

[![crates.io](https://img.shields.io/crates/v/iii-sdk)](https://crates.io/crates/iii-sdk)
[![docs.rs](https://img.shields.io/docsrs/iii-sdk)](https://docs.rs/iii-sdk)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](../../../LICENSE)

## Install

Add to your `Cargo.toml`:

```toml
[dependencies]
iii-sdk = "0.3"
serde_json = "1"
tokio = { version = "1", features = ["full"] }
```

## Quick Start

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

    iii.register_trigger("http", "greet", json!({
        "api_path": "greet",
        "http_method": "POST"
    }))?;

    let result: serde_json::Value = iii
        .trigger("greet", json!({ "name": "world" }))
        .await?;

    println!("result: {result}");
    Ok(())
}
```

## API

| Method | Description |
|--------|-------------|
| `III::new(url)` | Create an SDK instance |
| `iii.connect().await?` | Connect to the engine (sets up WebSocket + OTel) |
| `iii.register_function(id, \|input\| ...)` | Register a callable function |
| `iii.register_trigger(type, fn_id, config)?` | Bind a trigger to a function |
| `iii.trigger(id, data).await?` | Invoke a function and wait for the result |
| `iii.trigger_void(id, data)?` | Invoke a function without waiting (fire-and-forget) |

### Connection

Rust requires an explicit `iii.connect().await?` call. This starts a background task that handles WebSocket communication and automatic reconnection. It also sets up OpenTelemetry instrumentation.

### Streams

```rust
let stream = iii.stream();

stream.set("room.123", json!({ "users": ["alice", "bob"] })).await?;
let state = stream.get("room.123").await?;
```

### OpenTelemetry

Enable the `otel` feature for full tracing and metrics support:

```toml
[dependencies]
iii-sdk = { version = "0.3", features = ["otel"] }
```

## Notes

- `III::connect` starts a background task and handles reconnection automatically
- `register_function` does not return a handle (unlike the Node.js and Python SDKs)
- The engine protocol supports `registertriggertype` but does not include `unregistertriggertype`; `unregister_trigger_type` only removes local handlers

## Deprecated

`call()` is a deprecated alias for `trigger()`. It still works but will be removed in a future release.

## Resources

- [Documentation](https://iii.dev/docs)
- [iii Engine](https://github.com/iii-hq/iii)
- [Examples](https://github.com/iii-hq/iii-examples)
