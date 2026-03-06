from datetime import datetime


class MetricsStoreV0_1:

    def __init__(self):
        self.metrics = []

    def record(self, entry: dict):
        entry["timestamp"] = datetime.now().isoformat()
        self.metrics.append(entry)

    def get_all(self):
        return self.metrics

    def summary(self):
        return {
            "total_events": len(self.metrics)
        }