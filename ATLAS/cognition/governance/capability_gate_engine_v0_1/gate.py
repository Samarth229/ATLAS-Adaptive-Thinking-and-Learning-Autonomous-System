class CapabilityGateEngineV0_1:

    def evaluate(
        self,
        intent,
        confidence,
        state,
        meta_flags,
        identity
    ):

        dominant_emotion = state.get("dominant_emotion")

        if identity.get("operational_mode") == "restricted":
            return {
                "allowed": True,
                "mode": "restricted",
                "reason": "System in restricted operational mode."
            }

        if confidence < 0.3:
            return {
                "allowed": True,
                "mode": "restricted",
                "reason": "Low confidence intent classification."
            }

        if meta_flags.get("instability_detected"):
            return {
                "allowed": True,
                "mode": "safe_mode",
                "reason": "Meta instability detected."
            }

        if dominant_emotion == "stress":
            return {
                "allowed": True,
                "mode": "safe_mode",
                "reason": "Stress dominant state."
            }

        # IMPORTANT CHANGE HERE
        if intent == "unknown":
            return {
                "allowed": True,
                "mode": "normal",
                "reason": "Unstructured conversational intent."
            }

        return {
            "allowed": True,
            "mode": "normal",
            "reason": "No restrictions."
        }