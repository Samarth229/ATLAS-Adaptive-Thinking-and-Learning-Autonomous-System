class MemoryControllerV0_1:

    def __init__(
        self,
        goal_memory,
        emotion_memory,
        pattern_memory,
        profile_memory,
        interaction_logger,
        interaction_loader
    ):
        self.goal_memory = goal_memory
        self.emotion_memory = emotion_memory
        self.pattern_memory = pattern_memory
        self.profile_memory = profile_memory
        self.interaction_logger = interaction_logger
        self.interaction_loader = interaction_loader

    # -------------------------
    # READ OPERATIONS
    # -------------------------

    def get_goals(self):
        return self.goal_memory.list_goals()

    def get_recent_interactions(self, limit=5):
        return self.interaction_loader.load_recent(limit=limit)

    def get_profile(self):
        return self.profile_memory.load()

    def get_total_interactions(self):
        return self.interaction_loader.total_interactions()

    # -------------------------
    # WRITE OPERATIONS
    # -------------------------

    def record_emotion(self, emotion):
        self.emotion_memory.log_emotion(emotion)

    def record_pattern(self, text):
        self.pattern_memory.log_text(text)

    def record_interaction(self, user_input, system_response, version):
        self.interaction_logger.log(
            user_input=user_input,
            system_response=system_response,
            version=version
        )

    # -------------------------
    # FUTURE EXPANSION
    # -------------------------

    def build_context_window(self, limit=5):
        history = self.get_recent_interactions(limit)
        return {
            "recent_history": history,
            "goal_snapshot": self.get_goals(),
            "profile": self.get_profile()
        }