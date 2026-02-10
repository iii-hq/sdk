use super::connection::SharedEngineConnection;
use super::types::PREFIX_LOGS;
use opentelemetry_proto::tonic::collector::logs::v1::ExportLogsServiceRequest;
use opentelemetry_proto::transform::common::tonic::ResourceAttributesWithSchema;
use opentelemetry_proto::transform::logs::tonic::group_logs_by_resource_and_scope;
use opentelemetry_sdk::Resource;
use opentelemetry_sdk::error::OTelSdkResult;
use opentelemetry_sdk::logs::{LogBatch, LogExporter};
use std::fmt;
use std::sync::{Arc, Mutex};

/// Custom log exporter that sends OTLP JSON over a shared WebSocket connection
pub struct EngineLogExporter {
    connection: Arc<SharedEngineConnection>,
    resource: Mutex<Option<Resource>>,
}

impl EngineLogExporter {
    pub fn new(connection: Arc<SharedEngineConnection>) -> Self {
        Self {
            connection,
            resource: Mutex::new(None),
        }
    }
}

impl fmt::Debug for EngineLogExporter {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("EngineLogExporter")
            .field("resource", &self.resource)
            .finish()
    }
}

impl LogExporter for EngineLogExporter {
    async fn export(&self, batch: LogBatch<'_>) -> OTelSdkResult {
        if batch.iter().next().is_none() {
            return Ok(());
        }

        // Use builder().build() instead of default() for Resource
        let default_resource = Resource::builder().build();
        // Lock is acquired and released synchronously — no .await before drop
        let resource_guard = self.resource.lock().unwrap_or_else(|e| e.into_inner());
        let resource = resource_guard.as_ref().unwrap_or(&default_resource);
        let resource_attrs: ResourceAttributesWithSchema = resource.into();
        let resource_logs = group_logs_by_resource_and_scope(batch, &resource_attrs);

        let request = ExportLogsServiceRequest { resource_logs };

        let json = serde_json::to_vec(&request)
            .map_err(|e| opentelemetry_sdk::error::OTelSdkError::InternalFailure(e.to_string()))?;
        self.connection
            .send(PREFIX_LOGS, json)
            .map_err(opentelemetry_sdk::error::OTelSdkError::InternalFailure)
    }

    fn shutdown(&self) -> OTelSdkResult {
        Ok(())
    }

    fn set_resource(&mut self, resource: &Resource) {
        *self.resource.lock().unwrap_or_else(|e| e.into_inner()) = Some(resource.clone());
    }
}
