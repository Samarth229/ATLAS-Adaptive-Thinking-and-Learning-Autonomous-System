class TextEngineV0_1:

    def __init__(
        self,
        identity,
        session_history=None,
        profile=None,
        total_interactions=0,
        dominant_emotion=None
    ):
        self.identity = identity
        self.session_history = session_history or []
        self.profile = profile or {}
        self.total_interactions = total_interactions
        self.dominant_emotion = dominant_emotion

        self.stress_words = [
            "stressed",
            "overwhelmed",
            "pressure",
            "sad",
            "angry",
            "frustrated",
            "anxious"
        ]

        self.tired_words = [
            "tired",
            "exhausted",
            "sleepy",
            "drained"
        ]

        self.positive_words = [
            "happy",
            "excited",
            "motivated",
            "productive",
            "good",
            "calm"
        ]

    # ======================================================
    # PROFILE MANAGEMENT
    # ======================================================

    def update_profile(self, key, value):
        self.profile[key] = value

    # ======================================================
    # EMOTION DETECTION
    # ======================================================

    def detect_emotion(self, text: str):

        lowered = text.lower()

        if any(word in lowered for word in self.stress_words):
            return "stress"

        if any(word in lowered for word in self.tired_words):
            return "fatigue"

        if any(word in lowered for word in self.positive_words):
            return "positive"

        return None

    # ======================================================
    # RESPONSE GENERATION USING STATE ENGINE
    # ======================================================

    def generate_alignment_response(self, state):

        if state.get("goal_count", 0) == 0:
            return "No goals are currently defined."

        if state.get("alignment_status") == "aligned":
            return "You appear emotionally aligned with your current goals."

        return (
            "Your emotional strain may be affecting goal alignment. "
            "Consider adjusting pace or workload."
        )

    def generate_stability_response(self, state):

        score = state.get("stability_score", 0)

        return f"Emotional Stability Score: {score}"

    def generate_emotion_summary(self, state):

        analysis = state.get("raw_emotions")

        if not analysis:
            return "No emotional data available yet."

        total = sum(analysis.values())

        summary = "\n".join(
            f"{emotion.capitalize()}: {count}"
            for emotion, count in analysis.items()
        )

        return f"Recent Emotional Summary ({total} entries):\n{summary}"

    def generate_session_summary(self, session_emotions):

        total = sum(session_emotions.values())

        if total == 0:
            return "No emotional signals detected this session."

        summary = "\n".join(
            f"{emotion.capitalize()}: {count}"
            for emotion, count in session_emotions.items()
            if count > 0
        )

        return f"Session Emotional Summary ({total} entries):\n{summary}"

    # ======================================================
    # GREETING & IDENTITY
    # ======================================================

    def generate_greeting(self):

        if "name" in self.profile:

            name = self.profile["name"]

            if self.dominant_emotion == "stress":
                return f"Welcome back, {name}. Let's proceed steadily."

            if self.dominant_emotion == "fatigue":
                return f"Welcome back, {name}. Ensure you pace yourself."

            if self.dominant_emotion == "positive":
                return f"Good to see you again, {name}."

            return f"Welcome back, {name}."

        if self.session_history:
            return "Welcome back. I remember our recent interaction."

        return f"Hello. I am {self.identity['system_name']}."

    def generate_identity_response(self):

        if "name" in self.profile:
            return f"You are {self.profile['name']}."

        return "I do not yet know your name."

    def generate_status_response(self):
        return "System operational."

    # ======================================================
    # NAME EXTRACTION
    # ======================================================

    def extract_name(self, user_input: str):

        text = user_input.strip()
        lowered = text.lower()

        name_patterns = ["my name is", "call me"]

        for pattern in name_patterns:
            if lowered.startswith(pattern):

                candidate = text[len(pattern):].strip()

                return candidate if candidate else None

        if lowered.startswith("i am "):

            candidate = text[5:].strip()

            if candidate.lower() in (
                self.stress_words +
                self.tired_words +
                self.positive_words
            ):
                return None

            return candidate if candidate else None

        if lowered.startswith("i'm "):

            candidate = text[4:].strip()

            if candidate.lower() in (
                self.stress_words +
                self.tired_words +
                self.positive_words
            ):
                return None

            return candidate if candidate else None

        return None

    # ======================================================
    # GENERATIVE FALLBACK
    # ======================================================

    def process(self, user_input: str) -> str:

        emotion = self.detect_emotion(user_input)

        if emotion == "stress":
            return "I sense pressure in your tone. Let's approach this calmly."

        if emotion == "fatigue":
            return "You sound fatigued. Consider taking a short break."

        if emotion == "positive":
            return "That is good to hear. Maintain that momentum."

        return "Input received and logged."