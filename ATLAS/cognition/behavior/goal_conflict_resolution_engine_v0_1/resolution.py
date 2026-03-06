class GoalConflictResolutionEngineV0_1:

    def __init__(self):
        self.stability_override_threshold = -5

    def resolve(
        self,
        ranked_goals: list,
        state: dict
    ) -> dict:

        if not ranked_goals:
            return {
                "primary_goal": None,
                "deferred_goals": [],
                "conflict_detected": False
            }

        stability_score = state.get("stability_score", 0)
        dominant_emotion = state.get("dominant_emotion")

        conflict_detected = False

        primary_goal = ranked_goals[0]
        deferred_goals = ranked_goals[1:]

        # If instability severe → override to stability-preserving goal
        if stability_score <= self.stability_override_threshold:
            for goal in ranked_goals:
                if "rest" in goal["goal_text"].lower() or \
                   "balance" in goal["goal_text"].lower() or \
                   "health" in goal["goal_text"].lower():

                    primary_goal = goal
                    deferred_goals = [
                        g for g in ranked_goals if g != goal
                    ]
                    conflict_detected = True
                    break

        return {
            "primary_goal": primary_goal,
            "deferred_goals": deferred_goals,
            "conflict_detected": conflict_detected
        }