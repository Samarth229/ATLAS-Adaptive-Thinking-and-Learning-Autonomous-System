import re


class IntentEngineV0_1:

    def __init__(self):

        self.intent_labels = [
            "goal_alignment_query",
            "stability_query",
            "emotion_summary_query",
            "session_summary_query",
            "goal_creation",
            "goal_list_query",
            "progress_note",
            "emotion_statement",
            "identity_statement",
            "identity_query",
            "greeting",
            "unknown"
        ]

        self.emotion_keywords = [
            "stressed", "happy", "sad", "tired",
            "angry", "excited", "overwhelmed",
            "anxious", "frustrated", "motivated",
            "calm"
        ]

        self.goal_keywords = ["goal", "goals"]

        self.greeting_keywords = ["hi", "hello", "hey"]

    # -------------------------------------

    def _normalize(self, text: str):
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        return text.strip()

    # -------------------------------------

    def classify(self, text: str, previous_intent=None, previous_text=None):

        normalized = self._normalize(text)
        tokens = normalized.split()

        scores = {label: 0.0 for label in self.intent_labels}

        # =====================================================
        # GREETING
        # =====================================================

        if any(word in tokens for word in self.greeting_keywords):
            scores["greeting"] += 0.9

        # =====================================================
        # IDENTITY STATEMENT
        # =====================================================

        if normalized.startswith("my name is"):
            scores["identity_statement"] += 1.0

        elif normalized.startswith("i am ") or normalized.startswith("im "):
            if not any(word in tokens for word in self.emotion_keywords):
                scores["identity_statement"] += 0.7

        # =====================================================
        # IDENTITY QUERY
        # =====================================================

        if (
            ("what" in tokens and "name" in tokens) or
            ("who" in tokens and "i" in tokens) or
            ("tell" in tokens and "name" in tokens)
        ):
            scores["identity_query"] += 1.0

        # =====================================================
        # EMOTION STATEMENT
        # =====================================================

        emotion_hits = sum(
            1 for word in self.emotion_keywords if word in tokens
        )

        if emotion_hits > 0:
            scores["emotion_statement"] += min(0.6 + emotion_hits * 0.2, 1.0)

        # =====================================================
        # EMOTION SUMMARY (FIXED LOGIC)
        # =====================================================

        if "how" in tokens and "been" in tokens:

            if "session" in tokens:
                scores["session_summary_query"] += 1.0
            else:
                scores["emotion_summary_query"] += 0.9

        # =====================================================
        # STABILITY
        # =====================================================

        if "stable" in tokens or "stability" in tokens:
            scores["stability_query"] += 0.9

        # =====================================================
        # GOAL CREATION
        # =====================================================

        if normalized.startswith("my goal is"):
            scores["goal_creation"] += 1.0

        # =====================================================
        # GOAL LIST QUERY
        # =====================================================

        if any(word in tokens for word in self.goal_keywords):

            if any(q in tokens for q in ["what", "show", "list", "do"]):
                scores["goal_list_query"] += 0.9
            else:
                scores["goal_alignment_query"] += 0.5

        # =====================================================
        # PROGRESS NOTE
        # =====================================================

        if normalized.startswith("add note to goal"):
            scores["progress_note"] += 1.0

        # =====================================================
        # CONTEXT BOOSTING
        # =====================================================

        if previous_intent == "emotion_summary_query":
            if "stable" in tokens:
                scores["stability_query"] += 0.4

        if previous_intent == "goal_alignment_query":
            if "why" in tokens:
                scores["goal_alignment_query"] += 0.3

        # =====================================================

        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]

        if confidence == 0:
            return {
                "intent": "unknown",
                "confidence": 0.4
            }

        return {
            "intent": best_intent,
            "confidence": round(min(confidence, 1.0), 2)
        }