class PersonalityDriftEngineV0_1:
    def __init__(self):
        self.drift_threshold = 5
        self.stability_bias = 0.1

    def evaluate(
        self,
        state: dict,
        weight_memory
    ) -> dict:

        adjusted_state = state.copy()

        emotional_distribution = state.get("raw_emotions", {})
        dominant_emotion = state.get("dominant_emotion")

        stress = emotional_distribution.get("stress", 0)
        fatigue = emotional_distribution.get("fatigue", 0)
        positive = emotional_distribution.get("positive", 0)

        total = stress + fatigue + positive

        if total >= self.drift_threshold:

            if stress > positive:
                adjusted_state["personality_mode"] = "supportive"

            elif positive > stress:
                adjusted_state["personality_mode"] = "motivational"

            else:
                adjusted_state["personality_mode"] = "neutral"

        else:
            adjusted_state["personality_mode"] = "stable"

        return adjusted_state