import json
import os
from collections import defaultdict


class CognitiveWeightMemoryV0_1:
    def __init__(self):
        self.file_path = os.path.join(
            "memory",
            "structured",
            "cognitive_weights.json"
        )

        self.data = {
            "intent_frequency": {},
            "emotion_trend": {},
        }

        self._load()

    # --------------------------------------------------
    # Persistence Layer
    # --------------------------------------------------

    def _load(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                self.data = json.load(f)
        else:
            self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=4)

    # --------------------------------------------------
    # Intent Weight Tracking
    # --------------------------------------------------

    def update_intent(self, intent: str):
        freq = self.data["intent_frequency"].get(intent, 0)
        self.data["intent_frequency"][intent] = freq + 1
        self._save()

    def get_intent_multiplier(self, intent: str):
        freq = self.data["intent_frequency"].get(intent, 0)

        # Logarithmic scaling (stable long-term growth)
        if freq == 0:
            return 1.0

        return min(1.0 + (0.05 * (freq ** 0.5)), 1.5)

    # --------------------------------------------------
    # Emotion Trend Tracking
    # --------------------------------------------------

    def update_emotion(self, emotion: str):
        trend = self.data["emotion_trend"].get(emotion, 0)
        self.data["emotion_trend"][emotion] = trend + 1
        self._save()

    def get_emotion_bias(self, emotion: str):
        trend = self.data["emotion_trend"].get(emotion, 0)

        if trend == 0:
            return 1.0

        return min(1.0 + (0.03 * (trend ** 0.5)), 1.3)