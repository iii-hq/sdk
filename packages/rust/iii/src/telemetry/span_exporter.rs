use super::connection::SharedEngineConnection;
use super::types::PREFIX_TRACES;
use opentelemetry_proto::tonic::collector::trace::v1::ExportTraceServiceRequest;
use opentelemetry_proto::transform::common::tonic::ResourceAttributesWithSchema;
use opentelemetry_proto::transform::trace::tonic::group_spans_by_resource_and_scope;
use opentelemetry_sdk::error::OTelSdkResult;
use opentelemetry_sdk::trace::{SpanData, SpanExporter};
use opentelemetry_sdk::Resource;
use std::fmt;
use std::sync::{Arc, Mutex, OnceLock};

static EMPTY_RESOURCE: OnceLock<Resource> = OnceLock::new();

/// Custom span exporter that sends OTLP JSON over a shared WebSocket connection
pub struct EngineSpanExporter {
    connection: Arc<SharedEngineConnection>,
    resource: Mutex<Option<Resource>>,
}

impl EngineSpanExporter {
    pub fn new(connection: Arc<SharedEngineConnection>) -> Self {
        Self {
            connection,
            resource: Mutex::new(None),
        }
    }
}

impl fmt::Debug for EngineSpanExporter {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("EngineSpanExporter")
            .field("resource", &self.resource)
            .finish()
    }
}

impl SpanExporter for EngineSpanExporter {
    fn export(&self, batch: Vec<SpanData>) -> impl futures_util::Future<Output = OTelSdkResult> + Send {
        let is_empty = batch.is_empty();

        let resource = self.resource.lock().unwrap_or_else(|e| e.into_inner()).as_ref()
            .map(ResourceAttributesWithSchema::from)
            .unwrap_or_else(|| ResourceAttributesWithSchema::from(
                EMPTY_RESOURCE.get_or_init(|| Resource::builder_empty().build())
            ));

        let resource_spans = if is_empty {
            vec![]
        } else {
            group_spans_by_resource_and_scope(batch, &resource)
        };

        let request = ExportTraceServiceRequest { resource_spans };
        let connection = self.connection.clone();

        async move {
            if request.resource_spans.is_empty() {
                return Ok(());
            }

            let json = serde_json::to_vec(&request)
                .map_err(|e| opentelemetry_sdk::error::OTelSdkError::InternalFailure(e.to_string()))?;
            connection
                .send(PREFIX_TRACES, json)
                .map_err(opentelemetry_sdk::error::OTelSdkError::InternalFailure)
        }
    }

    fn shutdown(&mut self) -> OTelSdkResult {
        Ok(())
    }

    /// No-op: the synchronous SpanExporter trait cannot perform async I/O.
    /// Use `flush_otel()` for a full async flush of the connection layer.
    fn force_flush(&mut self) -> OTelSdkResult {
        Ok(())
    }

    fn set_resource(&mut self, resource: &Resource) {
        *self.resource.lock().unwrap_or_else(|e| e.into_inner()) = Some(resource.clone());
    }
}
