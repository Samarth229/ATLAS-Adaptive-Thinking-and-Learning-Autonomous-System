class DecisionArbitrationEngineV0_1:

    def __init__(self):
        pass

    def decide(
        self,
        intent: str,
        state: dict,
        meta_flags: dict,
        confidence: float,
        primary_goal: dict = None
    ) -> dict:

        dominant_emotion = state.get("dominant_emotion")
        stability_score = state.get("stability_score", 0)

        strategy = "direct"
        response_depth = "normal"
        escalation = False

        # Low confidence → clarifying strategy
        if confidence < 0.5:
            strategy = "clarifying"
            response_depth = "short"

        # Emotional instability → reflective or de-escalate
        elif stability_score < -5:
            strategy = "de_escalate"
            escalation = True

        elif dominant_emotion == "stress":
            strategy = "reflective"

        # Goal related intent → goal-oriented strategy
        elif "goal" in intent:
            strategy = "goal_oriented"

        # If a primary goal exists and intent aligns loosely,
        # bias toward goal-oriented behavior
        if primary_goal and strategy == "direct":
            strategy = "goal_oriented"

        # Meta conflict detected
        if meta_flags.get("conflict_detected"):
            strategy = "clarifying"

        # High confidence → deeper responses
        if confidence > 0.85:
            response_depth = "deep"

        return {
            "strategy": strategy,
            "response_depth": response_depth,
            "escalation": escalation
        }