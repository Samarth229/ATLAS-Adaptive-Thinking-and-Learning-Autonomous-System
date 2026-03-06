class BehavioralPolicyEngineV0_1:
    def __init__(self):
        self.verbosity_levels = {
            "low": 0,
            "normal": 1,
            "high": 2
        }

    # --------------------------------------------------
    # Core Modulation Method
    # --------------------------------------------------

    def modulate(
        self,
        response: str,
        state: dict,
        intent: str
    ) -> str:

        stability = state.get("stability_score", 0)
        dominant_emotion = state.get("dominant_emotion")

        response = self._apply_emotional_tone(
            response,
            dominant_emotion,
            stability
        )

        response = self._apply_intent_posture(
            response,
            intent
        )

        return response

    # --------------------------------------------------
    # Emotional Tone Adjustment
    # --------------------------------------------------

    def _apply_emotional_tone(
        self,
        response: str,
        dominant_emotion: str,
        stability: float
    ) -> str:

        if dominant_emotion == "stress":
            return f"{response} Take things one step at a time."

        if dominant_emotion == "fatigue":
            return f"{response} Consider pacing yourself."

        if dominant_emotion == "positive" and stability > 0:
            return f"{response} Keep building momentum."

        return response

    # --------------------------------------------------
    # Intent-Based Posture Adjustment
    # --------------------------------------------------

    def _apply_intent_posture(
        self,
        response: str,
        intent: str
    ) -> str:

        if intent == "goal_alignment_query":
            return f"{response} Alignment improves with consistent action."

        if intent == "stability_query":
            return f"{response} Stability trends fluctuate over time."

        return response