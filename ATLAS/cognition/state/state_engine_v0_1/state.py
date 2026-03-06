class CognitiveStateEngineV0_1:
    def __init__(self, emotion_memory, goal_memory):
        self.emotion_memory = emotion_memory
        self.goal_memory = goal_memory

    def build_state(self, emotion_limit=20):
        analysis = self.emotion_memory.analyze_recent(limit=emotion_limit)
        goals = self.goal_memory.list_goals()

        if not analysis:
            analysis = {}

        stress = analysis.get("stress", 0)
        fatigue = analysis.get("fatigue", 0)
        positive = analysis.get("positive", 0)

        dominant_emotion = None
        if analysis:
            dominant_emotion = max(analysis, key=analysis.get)

        stability_score = positive - (stress + fatigue)

        emotional_load = stress + fatigue

        if positive >= emotional_load:
            alignment_status = "aligned"
        else:
            alignment_status = "misaligned"

        if emotional_load == 0:
            emotional_pressure = "low"
        elif emotional_load < positive:
            emotional_pressure = "moderate"
        else:
            emotional_pressure = "elevated"

        state = {
            "dominant_emotion": dominant_emotion,
            "stability_score": stability_score,
            "goal_count": len(goals),
            "alignment_status": alignment_status,
            "emotional_pressure": emotional_pressure,
            "raw_emotions": analysis
        }

        return state