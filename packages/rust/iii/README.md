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
| `iii.register_function(id, \|input\| ...)` | Register a function that can be invoked by name |
| `iii.register_trigger(type, fn_id, config)?` | Bind a trigger (HTTP, cron, queue, etc.) to a function |
| `iii.register_trigger_type(id, description, handler)` | Register a custom trigger type |
| `iii.trigger(id, data).await?` | Invoke a function and wait for the result |
| `iii.trigger_void(id, data)?` | Invoke a function without waiting (fire-and-forget) |

### Connection

Rust requires an explicit `iii.connect().await?` call. This starts a background task that handles WebSocket communication and automatic reconnection. It also sets up OpenTelemetry instrumentation.

### Registering Functions

```rust
iii.register_function("math.add", |input| async move {
    let a = input["a"].as_i64().unwrap_or(0);
    let b = input["b"].as_i64().unwrap_or(0);
    Ok(json!({ "sum": a + b }))
});
```

### Registering Triggers

```rust
iii.register_trigger("http", "math.add", json!({
    "api_path": "add",
    "http_method": "POST"
}))?;
```

### Custom Trigger Types

```rust
iii.register_trigger_type("webhook", "External webhook trigger", my_handler);
```

### Invoking Functions

```rust
let result = iii.trigger("math.add", json!({ "a": 2, "b": 3 })).await?;

iii.trigger_void("analytics.track", json!({ "event": "page_view" }))?;
```

### Streams

```rust
use iii_sdk::Streams;

let streams = Streams::new(iii.clone());
streams.set_field("room::123", "users", json!(["alice", "bob"])).await?;
```

### OpenTelemetry

Enable the `otel` feature for full tracing and metrics support:

```toml
[dependencies]
iii-sdk = { version = "0.3", features = ["otel"] }
```

## Deprecated

`call()` and `call_void()` are deprecated aliases for `trigger()` and `trigger_void()`. They still work but will be removed in a future release.

## Resources

- [Documentation](https://iii.dev/docs)
- [iii Engine](https://github.com/iii-hq/iii)
- [Examples](https://github.com/iii-hq/iii-examples)
