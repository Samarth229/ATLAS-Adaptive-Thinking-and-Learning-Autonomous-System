import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
LOG_PATH = BASE_DIR / "memory" / "interactions" / "interaction_log.jsonl"

class InteractionLoaderV0_1:

    def load_recent(self, limit=5):
        if not LOG_PATH.exists():
            return []

        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        recent = lines[-limit:]
        return [json.loads(line) for line in recent]
    
    def total_interactions(self):
        if not LOG_PATH.exists():
            return 0

        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return len(f.readlines())