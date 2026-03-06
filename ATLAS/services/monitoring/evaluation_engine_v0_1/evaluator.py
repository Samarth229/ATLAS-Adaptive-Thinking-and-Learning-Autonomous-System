class EvaluationEngineV0_1:

    def __init__(self, metrics_store):
        self.metrics_store = metrics_store

    def record_model_call(self, source, latency, confidence):
        self.metrics_store.record({
            "type": "model_call",
            "source": source,
            "latency_ms": latency,
            "confidence": confidence
        })

    def record_gate_event(self, mode, reason):
        self.metrics_store.record({
            "type": "gate_event",
            "mode": mode,
            "reason": reason
        })

    def record_tool_execution(self, tool_name, success):
        self.metrics_store.record({
            "type": "tool_execution",
            "tool": tool_name,
            "success": success
        })

    def record_error(self, error_message):
        self.metrics_store.record({
            "type": "error",
            "message": error_message
        })