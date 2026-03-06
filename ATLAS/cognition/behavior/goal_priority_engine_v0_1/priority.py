import math


class GoalPriorityEngineV0_1:
    def __init__(self, goal_memory, state_engine, weight_memory):
        self.goal_memory = goal_memory
        self.state_engine = state_engine
        self.weight_memory = weight_memory

    # --------------------------------------------------
    # Core Priority Calculation
    # --------------------------------------------------

    def compute_priorities(self):
        goals = self.goal_memory.list_goals()
        state = self.state_engine.build_state()

        if not goals:
            return []

        stability = state.get("stability_score", 0)
        emotional_load = (
            state["raw_emotions"].get("stress", 0) +
            state["raw_emotions"].get("fatigue", 0)
        )

        ranked_goals = []

        for index, goal in enumerate(goals):
            base_score = 1.0

            # ---------------------------------
            # Emotional Influence
            # ---------------------------------
            if stability < 0:
                base_score += abs(stability) * 0.1

            if emotional_load > 0:
                base_score += math.log1p(emotional_load) * 0.2

            # ---------------------------------
            # Progress Depth Influence
            # ---------------------------------
            progress_count = len(goal.get("progress_notes", []))
            base_score += progress_count * 0.15

            # ---------------------------------
            # Intent Frequency Influence
            # ---------------------------------
            intent_multiplier = self.weight_memory.get_intent_multiplier(
                "goal_alignment_query"
            )

            base_score *= intent_multiplier

            ranked_goals.append({
                "goal_index": index,
                "goal_text": goal["goal"],
                "priority_score": round(base_score, 3)
            })

        ranked_goals.sort(
            key=lambda x: x["priority_score"],
            reverse=True
        )

        return ranked_goals