import json
from pathlib import Path
from datetime import datetime


class ReflectionEngineV0_1:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parents[3]
        self.emotion_log_path = self.base_dir / "memory" / "structured" / "emotion_log.jsonl"
        self.reflection_dir = self.base_dir / "memory" / "reflections"

        self.reflection_dir.mkdir(parents=True, exist_ok=True)

    def load_recent_emotions(self, limit=30):
        if not self.emotion_log_path.exists():
            return []

        with open(self.emotion_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        recent = lines[-limit:]

        emotions = []
        for line in recent:
            try:
                data = json.loads(line.strip())
                emotions.append(data.get("emotion"))
            except:
                continue

        return emotions

    def analyze(self, emotions):
        if not emotions:
            return None, {}

        counts = {}
        for e in emotions:
            counts[e] = counts.get(e, 0) + 1

        dominant = max(counts, key=counts.get)
        return dominant, counts

    def generate_reflection(self, dominant_emotion, counts):
        total = sum(counts.values())

        if dominant_emotion == "stress":
            message = (
                "I have observed a recurring stress pattern recently. "
                "It may be beneficial to adjust workload pacing."
            )

        elif dominant_emotion == "fatigue":
            message = (
                "Fatigue signals have appeared consistently. "
                "Rest optimization may be necessary."
            )

        elif dominant_emotion == "positive":
            message = (
                "A positive emotional trend is evident. "
                "Momentum appears stable."
            )

        else:
            message = "Emotional distribution appears balanced."

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dominant_emotion": dominant_emotion,
            "total_entries": total,
            "distribution": counts,
            "reflection": message
        }

    def save_reflection(self, reflection_data):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.reflection_dir / f"reflection_{timestamp}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(reflection_data, f, indent=4)

    def run_reflection(self):
        emotions = self.load_recent_emotions(limit=30)

        dominant, counts = self.analyze(emotions)

        if not dominant:
            return None

        reflection_data = self.generate_reflection(dominant, counts)

        self.save_reflection(reflection_data)

        return reflection_data["reflection"]