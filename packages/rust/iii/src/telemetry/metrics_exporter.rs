use super::connection::SharedEngineConnection;
use super::types::PREFIX_METRICS;
use opentelemetry_proto::tonic::collector::metrics::v1::ExportMetricsServiceRequest;
use opentelemetry_sdk::error::OTelSdkResult;
use opentelemetry_sdk::metrics::data::ResourceMetrics;
use opentelemetry_sdk::metrics::exporter::PushMetricExporter;
use opentelemetry_sdk::metrics::Temporality;
use std::fmt;
use std::sync::Arc;

/// Custom metrics exporter that sends OTLP JSON over a shared WebSocket connection
pub struct EngineMetricsExporter {
    connection: Arc<SharedEngineConnection>,
}

impl EngineMetricsExporter {
    pub fn new(connection: Arc<SharedEngineConnection>) -> Self {
        Self { connection }
    }
}

impl fmt::Debug for EngineMetricsExporter {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("EngineMetricsExporter").finish()
    }
}

impl PushMetricExporter for EngineMetricsExporter {
    fn export(&self, metrics: &ResourceMetrics) -> impl std::future::Future<Output = OTelSdkResult> + Send {
        let request = ExportMetricsServiceRequest::from(metrics);
        let connection = self.connection.clone();
        async move {
            let json = serde_json::to_vec(&request)
                .map_err(|e| opentelemetry_sdk::error::OTelSdkError::InternalFailure(e.to_string()))?;
            connection
                .send(PREFIX_METRICS, json)
                .map_err(opentelemetry_sdk::error::OTelSdkError::InternalFailure)
        }
    }

    /// No-op: the synchronous PushMetricExporter trait cannot perform async I/O.
    /// Use `flush_otel()` for a full async flush of the connection layer.
    fn force_flush(&self) -> OTelSdkResult {
        Ok(())
    }

    fn shutdown(&self) -> OTelSdkResult {
        Ok(())
    }

    fn shutdown_with_timeout(&self, _timeout: std::time::Duration) -> OTelSdkResult {
        Ok(())
    }

    fn temporality(&self) -> Temporality {
        Temporality::Cumulative
    }
}
