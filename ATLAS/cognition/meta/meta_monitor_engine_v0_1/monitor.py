class MetaCognitiveMonitorEngineV0_1:
    def __init__(self):
        self.low_confidence_threshold = 0.5
        self.volatility_threshold = 3

    def evaluate(
        self,
        intent: str,
        confidence: float,
        state: dict,
        previous_intent: str = None
    ) -> dict:

        flags = {
            "low_confidence": False,
            "intent_shift": False,
            "emotional_volatility": False
        }

        # --- Low confidence detection ---
        if confidence < self.low_confidence_threshold:
            flags["low_confidence"] = True

        # --- Intent shift detection ---
        if previous_intent and previous_intent != intent:
            flags["intent_shift"] = True

        # --- Emotional volatility detection ---
        emotions = state.get("raw_emotions", {})
        stress = emotions.get("stress", 0)
        positive = emotions.get("positive", 0)

        if abs(stress - positive) > self.volatility_threshold:
            flags["emotional_volatility"] = True

        return flags