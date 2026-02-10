pub mod context;
pub mod error;
pub mod iii;
pub mod logger;
pub mod protocol;
pub mod streams;
#[cfg(feature = "otel")]
pub mod telemetry;
pub mod triggers;
pub mod types;

pub use context::{Context, get_context, with_context};
pub use error::IIIError;
pub use iii::{
    FunctionInfo, FunctionsAvailableGuard, III, TriggerInfo, WorkerInfo, WorkerMetadata,
};
pub use logger::{Logger, LoggerInvoker};
pub use protocol::{
    ErrorBody, FunctionMessage, Message, RegisterFunctionMessage, RegisterServiceMessage,
    RegisterTriggerMessage, RegisterTriggerTypeMessage,
};
pub use streams::{Streams, UpdateBuilder};
pub use triggers::{Trigger, TriggerConfig, TriggerHandler};
pub use types::{ApiRequest, ApiResponse, FieldPath, StreamUpdateInput, UpdateOp, UpdateResult};

pub use serde_json::Value;

// OpenTelemetry re-exports (behind "otel" feature flag)
#[cfg(feature = "otel")]
pub use telemetry::{
    init_otel, shutdown_otel, flush_otel, with_span, get_tracer, get_meter, is_initialized,
    types::OtelConfig,
    types::ReconnectionConfig,
    context::{
        current_trace_id, current_span_id,
        inject_traceparent, extract_traceparent,
        inject_baggage, extract_baggage, extract_context,
        get_baggage_entry, set_baggage_entry, remove_baggage_entry, get_all_baggage,
    },
};

// Re-export commonly used OpenTelemetry types for convenience
#[cfg(feature = "otel")]
pub use opentelemetry::trace::SpanKind;
#[cfg(feature = "otel")]
pub use opentelemetry::trace::Status as SpanStatus;
