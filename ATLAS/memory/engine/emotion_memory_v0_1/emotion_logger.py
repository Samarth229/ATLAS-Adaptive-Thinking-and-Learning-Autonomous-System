import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[3]
EMOTION_LOG = BASE_DIR / "memory" / "structured" / "emotion_log.jsonl"

class EmotionMemoryV0_1:

    def log_emotion(self, emotion_type):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "emotion": emotion_type
        }

        EMOTION_LOG.parent.mkdir(parents=True, exist_ok=True)

        with open(EMOTION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def analyze_recent(self, limit=20):
        if not EMOTION_LOG.exists():
            return {}

        with open(EMOTION_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()

        recent = lines[-limit:]

        counts = {}

        for line in recent:
            data = json.loads(line)
            emotion = data.get("emotion")

            if emotion:
                counts[emotion] = counts.get(emotion, 0) + 1

        return counts