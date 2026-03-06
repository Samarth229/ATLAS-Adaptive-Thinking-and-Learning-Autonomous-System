class AtlasEngineV0_2:

    def __init__(
        self,
        model,
        text_engine,
        intent_engine,
        identity,
        goal_memory,
        session_emotions,
        state_engine,
        emotion_memory
    ):
        self.model = model
        self.text_engine = text_engine
        self.intent_engine = intent_engine
        self.identity = identity
        self.goal_memory = goal_memory
        self.session_emotions = session_emotions
        self.state_engine = state_engine
        self.emotion_memory = emotion_memory

    # =========================================================
    # PUBLIC ENTRY POINT
    # =========================================================

    def process(self, payload: str) -> dict:

        classification = self.intent_engine.classify(
            payload,
            previous_intent=self.identity.get("last_intent"),
            previous_text=self.identity.get("last_input")
        )

        intent = classification.get("intent", "unknown")
        confidence = classification.get("confidence", 0.0)

        response_text = self._route_intent(intent, payload)

        self.identity["last_intent"] = intent
        self.identity["last_input"] = payload

        detected_emotion = self.text_engine.detect_emotion(payload)

        if detected_emotion:

            if detected_emotion in self.session_emotions:
                self.session_emotions[detected_emotion] += 1

            try:
                self.emotion_memory.log_emotion(detected_emotion)
            except Exception:
                pass

        return {
            "intent": intent,
            "confidence": confidence,
            "text": response_text,
            "meta": {
                "engine_version": "0.2",
                "routing_layer": "core",
                "model_used": getattr(self.model, "__class__", type(self.model)).__name__
            }
        }

    # =========================================================
    # INTERNAL ROUTING
    # =========================================================

    def _route_intent(self, intent: str, payload: str) -> str:

        # ------------------------------
        # Greeting
        # ------------------------------

        if intent == "greeting":
            return self.text_engine.generate_greeting()

        # ------------------------------
        # Identity
        # ------------------------------

        if intent == "identity_statement":

            extracted_name = self.text_engine.extract_name(payload)

            if extracted_name:
                self.identity["name"] = extracted_name
                self.text_engine.update_profile("name", extracted_name)
                return f"I will remember that. Your name is {extracted_name}."

            return "I could not determine your name."

        if intent == "identity_query":
            return self.text_engine.generate_identity_response()

        # ------------------------------
        # Emotion Handling
        # ------------------------------

        if intent == "emotion_statement":

            emotion = self.text_engine.detect_emotion(payload)

            if emotion == "stress":
                return "I sense pressure in your tone. Let's approach this calmly."

            if emotion == "fatigue":
                return "You sound fatigued. Consider taking a short break."

            if emotion == "positive":
                return "That is good to hear. Maintain that momentum."

            return "I acknowledge your emotional state."

        # ------------------------------
        # Long-term Emotional Summary
        # ------------------------------

        if intent == "emotion_summary_query":

            state = self.state_engine.build_state()

            return self.text_engine.generate_emotion_summary(state)

        # ------------------------------
        # Session Emotional Summary
        # ------------------------------

        if intent == "session_summary_query":

            return self.text_engine.generate_session_summary(self.session_emotions)

        # ------------------------------
        # Stability
        # ------------------------------

        if intent == "stability_query":

            stress = self.session_emotions.get("stress", 0)
            fatigue = self.session_emotions.get("fatigue", 0)
            positive = self.session_emotions.get("positive", 0)

            stability_score = positive - (stress + fatigue)

            return f"Emotional Stability Score: {stability_score}"

        # ------------------------------
        # Goals
        # ------------------------------

        if intent == "goal_creation":

            goal_text = payload.lower().replace("my goal is", "").strip()

            if goal_text:
                self.goal_memory.add_goal(goal_text)
                return f"Goal added: {goal_text}"

            return "Please specify the goal clearly."

        if intent == "goal_list_query":

            goals = self.goal_memory.list_goals()

            if not goals:
                return "You do not have any goals defined yet."

            formatted = "\n".join(
                f"{idx + 1}. {goal['goal']}"
                for idx, goal in enumerate(goals)
            )

            return f"Your Goals:\n{formatted}"

        if intent == "progress_note":

            parts = payload.lower().split()

            try:
                goal_index = int(parts[4]) - 1
            except (IndexError, ValueError):
                return "Invalid goal index specified."

            note_text = " ".join(parts[5:]).strip()

            if not note_text:
                return "Please provide a progress note."

            success = self.goal_memory.add_progress_note(goal_index, note_text)

            if success:
                return f"Progress note added to goal {goal_index + 1}."

            return "Goal not found."

        if intent == "goal_alignment_query":

            state = self.state_engine.build_state()

            return self.text_engine.generate_alignment_response(state)

        # ------------------------------
        # Unknown / Generative Fallback
        # ------------------------------

        return self._generate_with_model(payload)

    # =========================================================
    # MODEL WRAPPER
    # =========================================================

    def _generate_with_model(self, payload: str) -> str:

        try:

            model_output = self.model.route(prompt=payload)

            if isinstance(model_output, dict):
                return model_output.get(
                    "text",
                    "I am unable to produce a response at the moment."
                )

            return str(model_output)

        except Exception:
            return "An internal processing error occurred."