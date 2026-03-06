import time
import threading
from rich.console import Console

from services.daemon.event_bus import EventBus

from cognition.intent_engine_v0_1.intent import IntentEngineV0_1
from cognition.reasoning.text_engine_v0_1.engine import TextEngineV0_1
from cognition.state.state_engine_v0_1.state import CognitiveStateEngineV0_1
from cognition.behavior.goal_priority_engine_v0_1.priority import GoalPriorityEngineV0_1
from cognition.behavior.goal_conflict_resolution_engine_v0_1.resolution import GoalConflictResolutionEngineV0_1
from cognition.behavior.behavioral_policy_engine_v0_1.policy import BehavioralPolicyEngineV0_1
from cognition.behavior.decision_arbitration_engine_v0_1.arbitration import DecisionArbitrationEngineV0_1
from cognition.identity.personality_drift_engine_v0_1.drift import PersonalityDriftEngineV0_1
from cognition.meta.meta_monitor_engine_v0_1.monitor import MetaCognitiveMonitorEngineV0_1
from cognition.meta.adaptive_clarification_engine_v0_1.clarifier import AdaptiveClarificationEngineV0_1
from cognition.meta.confidence_response_engine_v0_1.depth import ConfidenceAdaptiveResponseEngineV0_1
from cognition.meta.volatility_reflection_engine_v0_1.reflection import VolatilityReflectionEngineV0_1
from cognition.governance.capability_gate_engine_v0_1.gate import CapabilityGateEngineV0_1

from memory.engine.interaction_logger_v0_1.logger import InteractionLoggerV0_1
from memory.engine.interaction_loader_v0_1.loader import InteractionLoaderV0_1
from memory.engine.profile_memory_v0_1.profile import ProfileMemoryV0_1
from memory.engine.emotion_memory_v0_1.emotion_logger import EmotionMemoryV0_1
from memory.engine.reflection_engine_v0_1.reflection import ReflectionEngineV0_1
from memory.engine.pattern_memory_v0_1.pattern import PatternMemoryV0_1
from memory.engine.goal_memory_v0_1.goal import GoalMemoryV0_1
from memory.engine.cognitive_weight_memory_v0_1.weight import CognitiveWeightMemoryV0_1


console = Console()
shutdown_event = threading.Event()


def start_runtime(identity):
    console.print("[bold yellow]A.T.L.A.S entering interactive runtime (v0.4)...[/bold yellow]")

    event_bus = EventBus()

    interaction_loader = InteractionLoaderV0_1()
    recent_history = interaction_loader.load_recent(limit=5)
    total_interactions = interaction_loader.total_interactions()

    profile_memory = ProfileMemoryV0_1()
    profile_data = profile_memory.load()

    emotion_memory = EmotionMemoryV0_1()
    reflection_engine = ReflectionEngineV0_1()
    pattern_memory = PatternMemoryV0_1()
    goal_memory = GoalMemoryV0_1()
    weight_memory = CognitiveWeightMemoryV0_1()

    state_engine = CognitiveStateEngineV0_1(
        emotion_memory,
        goal_memory
    )

    goal_priority_engine = GoalPriorityEngineV0_1(
        goal_memory,
        state_engine,
        weight_memory
    )

    goal_conflict_engine = GoalConflictResolutionEngineV0_1()
    behavioral_policy_engine = BehavioralPolicyEngineV0_1()
    arbitration_engine = DecisionArbitrationEngineV0_1()
    personality_drift_engine = PersonalityDriftEngineV0_1()
    meta_monitor_engine = MetaCognitiveMonitorEngineV0_1()
    clarification_engine = AdaptiveClarificationEngineV0_1()
    confidence_engine = ConfidenceAdaptiveResponseEngineV0_1()
    volatility_reflection_engine = VolatilityReflectionEngineV0_1()

    # 🔒 Phase 42 Engine
    capability_gate_engine = CapabilityGateEngineV0_1()

    intent_engine = IntentEngineV0_1()

    text_engine = TextEngineV0_1(
        identity,
        recent_history,
        profile_data,
        total_interactions,
        state_engine.build_state()["dominant_emotion"]
    )

    interaction_logger = InteractionLoggerV0_1()

    event_bus.publish("system_started")

    input_thread = threading.Thread(
        target=listen_for_input,
        args=(event_bus,),
        daemon=True
    )
    input_thread.start()

    try:
        while not shutdown_event.is_set():
            event = event_bus.get_event()

            if event:
                handle_event(
                    event,
                    text_engine,
                    interaction_logger,
                    identity,
                    emotion_memory,
                    pattern_memory,
                    state_engine,
                    intent_engine,
                    weight_memory,
                    goal_priority_engine,
                    goal_conflict_engine,
                    behavioral_policy_engine,
                    arbitration_engine,
                    personality_drift_engine,
                    meta_monitor_engine,
                    clarification_engine,
                    confidence_engine,
                    volatility_reflection_engine,
                    capability_gate_engine
                )

            time.sleep(0.1)

    except KeyboardInterrupt:
        shutdown_event.set()

    finally:
        console.print("\n[bold red]Shutdown signal received.[/bold red]")
        console.print("[bold cyan]A.T.L.A.S shutting down safely.[/bold cyan]")


def listen_for_input(event_bus):
    while not shutdown_event.is_set():
        try:
            user_input = input(">> ")
            event_bus.publish("text_input", user_input)
        except (EOFError, KeyboardInterrupt):
            shutdown_event.set()


def handle_event(
    event,
    text_engine,
    interaction_logger,
    identity,
    emotion_memory,
    pattern_memory,
    state_engine,
    intent_engine,
    weight_memory,
    goal_priority_engine,
    goal_conflict_engine,
    behavioral_policy_engine,
    arbitration_engine,
    personality_drift_engine,
    meta_monitor_engine,
    clarification_engine,
    confidence_engine,
    volatility_reflection_engine,
    capability_gate_engine
):
    event_type = event["type"]
    payload = event["payload"]

    if event_type == "text_input":

        state = state_engine.build_state()

        adjusted_state = personality_drift_engine.evaluate(
            state=state,
            weight_memory=weight_memory
        )

        result = intent_engine.classify(
            payload,
            previous_intent=identity.get("last_intent"),
            previous_text=identity.get("last_input")
        )

        intent = result["intent"]
        base_confidence = result["confidence"]
        multiplier = weight_memory.get_intent_multiplier(intent)
        confidence = round(min(base_confidence * multiplier, 1.0), 2)

        console.print(f"[dim]Detected intent: {intent} (confidence: {confidence})[/dim]")

        meta_flags = meta_monitor_engine.evaluate(
            intent=intent,
            confidence=confidence,
            state=adjusted_state,
            previous_intent=identity.get("last_intent")
        )

        ranked_goals = goal_priority_engine.compute_priorities()

        conflict_result = goal_conflict_engine.resolve(
            ranked_goals=ranked_goals,
            state=adjusted_state
        )

        arbitration_result = arbitration_engine.decide(
            intent=intent,
            state=adjusted_state,
            meta_flags=meta_flags,
            confidence=confidence,
            primary_goal=conflict_result["primary_goal"]
        )

        strategy = arbitration_result["strategy"]

        # 🔒 PHASE 42 — Capability Gate
        gate_result = capability_gate_engine.evaluate(
            intent=intent,
            confidence=confidence,
            state=adjusted_state,
            meta_flags=meta_flags,
            identity=identity
        )

        console.print(f"[dim]Gate Mode: {gate_result['mode']} | Reason: {gate_result['reason']}[/dim]")

        if not gate_result["allowed"]:
            final_response = "I cannot respond to that request."
        else:

            if gate_result["mode"] == "safe_mode":
                response = "Let's proceed carefully. Could you provide more clarity?"

            elif gate_result["mode"] == "restricted":
                response = "I may need more information before proceeding."

            else:
                if strategy == "clarifying":
                    response = "Could you clarify what you mean?"
                elif strategy == "de_escalate":
                    response = "Let's slow down and approach this calmly."
                elif strategy == "reflective":
                    response = text_engine.generate_emotion_summary(adjusted_state)
                elif strategy == "goal_oriented":
                    if conflict_result["primary_goal"]:
                        response = f"Primary Goal Focus: {conflict_result['primary_goal']['goal_text']}"
                    else:
                        response = "No goals recorded yet."
                else:
                    response = text_engine.process(payload)

            response = behavioral_policy_engine.modulate(
                response=response,
                state=adjusted_state,
                intent=intent
            )

            response = confidence_engine.adapt(
                response=response,
                confidence=confidence
            )

            clarification_result = clarification_engine.evaluate(
                response=response,
                meta_flags=meta_flags,
                intent=intent
            )

            final_response = clarification_result["final_response"]

        console.print(f"[cyan]{final_response}[/cyan]")

        identity["last_intent"] = intent
        identity["last_input"] = payload
        identity["last_meta_flags"] = meta_flags

        weight_memory.update_intent(intent)

        emotion = text_engine.detect_emotion(payload)
        if emotion:
            emotion_memory.log_emotion(emotion)
            weight_memory.update_emotion(emotion)

        pattern_memory.log_text(payload)

        interaction_logger.log(
            user_input=payload,
            system_response=final_response,
            version=identity["version"]
        )