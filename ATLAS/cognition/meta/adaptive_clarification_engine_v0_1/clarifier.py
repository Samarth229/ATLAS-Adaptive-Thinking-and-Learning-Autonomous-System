class AdaptiveClarificationEngineV0_1:

    def __init__(self):
        self.low_confidence_threshold = 0.5

        self.safe_intents = [
            "emotion_statement",
            "greeting",
            "identity_statement",
            "identity_query",
            "goal_list_query",
            "emotion_summary_query",
            "session_summary_query"
        ]

    def evaluate(
        self,
        response: str,
        meta_flags: dict,
        intent: str
    ) -> dict:

        result = {
            "should_clarify": False,
            "final_response": response
        }

        # --------------------------------------------------
        # DO NOT CLARIFY FOR SAFE INTENTS
        # --------------------------------------------------

        if intent in self.safe_intents:
            return result

        # --------------------------------------------------
        # LOW CONFIDENCE → Clarify
        # --------------------------------------------------

        if meta_flags.get("low_confidence"):
            result["should_clarify"] = True
            result["final_response"] = (
                "I may need clarification to respond accurately. "
                "Could you rephrase or expand on that?"
            )
            return result

        # --------------------------------------------------
        # STRONG INTENT SHIFT → Clarify
        # --------------------------------------------------

        if meta_flags.get("intent_shift"):
            result["should_clarify"] = True
            result["final_response"] = (
                "I noticed a shift in your request. "
                "Would you like to continue with the new direction?"
            )
            return result

        return result