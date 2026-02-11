//! Backward-compatible aliases for the legacy `iii` module.
//!
//! The SDK now uses `Bridge`/`BridgeError` naming.
//! Keep these exports so existing `iii::III` imports continue to work.

pub use crate::bridge::{
    Bridge as III,
    FunctionInfo,
    FunctionsAvailableGuard,
    TriggerInfo,
    WorkerInfo,
    WorkerMetadata,
};
