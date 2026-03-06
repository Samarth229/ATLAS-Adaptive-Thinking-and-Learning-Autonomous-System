import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[3]
LOG_PATH = BASE_DIR / "memory" / "interactions" / "interaction_log.jsonl"

class InteractionLoggerV0_1:

    def log(self, user_input, system_response, version):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_input": user_input,
            "system_response": system_response,
            "system_version": version
        }

        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")