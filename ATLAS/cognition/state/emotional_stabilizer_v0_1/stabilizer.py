class EmotionalStabilizerEngineV0_1:

    def __init__(self, session_emotions: dict):
        self.session_emotions = session_emotions

    def stabilize(self, raw_state: dict) -> dict:

        historical_emotions = raw_state.get("emotion_distribution", {})
        stability_score = raw_state.get("stability_score", 0)

        adjusted_distribution = {}

        for emotion, historical_score in historical_emotions.items():

            session_score = self.session_emotions.get(emotion, 0)

            adjusted_score = (
                (historical_score * 0.7) +
                (session_score * 1.5)
            )

            adjusted_distribution[emotion] = round(adjusted_score, 2)

        if adjusted_distribution:
            dominant_emotion = max(
                adjusted_distribution,
                key=adjusted_distribution.get
            )
        else:
            dominant_emotion = None

        # Recalculate stability lightly
        if dominant_emotion == "stress":
            stability_score -= 1
        elif dominant_emotion == "positive":
            stability_score += 1

        stabilized_state = raw_state.copy()
        stabilized_state["emotion_distribution"] = adjusted_distribution
        stabilized_state["dominant_emotion"] = dominant_emotion
        stabilized_state["stability_score"] = stability_score

        return stabilized_state