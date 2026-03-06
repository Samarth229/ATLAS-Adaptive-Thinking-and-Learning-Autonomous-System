import time
import threading
from rich.console import Console
from .event_bus import EventBus
from cognition.reasoning.text_engine_v0_1.engine import TextEngineV0_1
from memory.engine.interaction_logger_v0_1.logger import InteractionLoggerV0_1
from memory.engine.interaction_loader_v0_1.loader import InteractionLoaderV0_1
from memory.engine.profile_memory_v0_1.profile import ProfileMemoryV0_1
from memory.engine.emotion_memory_v0_1.emotion_logger import EmotionMemoryV0_1
from memory.engine.reflection_engine_v0_1.reflection import ReflectionEngineV0_1
from memory.engine.pattern_memory_v0_1.pattern import PatternMemoryV0_1
from memory.engine.goal_memory_v0_1.goal import GoalMemoryV0_1

console = Console()
shutdown_event = threading.Event()


def start_runtime(identity):
    console.print("[bold yellow]A.T.L.A.S entering interactive runtime (v0.3)...[/bold yellow]")

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

    analysis = emotion_memory.analyze_recent(limit=20)
    dominant_emotion = max(analysis, key=analysis.get) if analysis else None

    session_emotions = {
        "stress": 0,
        "fatigue": 0,
        "positive": 0
    }

    text_engine = TextEngineV0_1(
        identity,
        recent_history,
        profile_data,
        total_interactions,
        dominant_emotion
    )

    interaction_logger = InteractionLoggerV0_1()

    boot_count = identity.get("boot_count", 0)

    if boot_count % 5 == 0:
        reflection_message = reflection_engine.run_reflection()
        if reflection_message:
            console.print(f"[bold magenta]Reflection:[/bold magenta] {reflection_message}")

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
                    profile_memory,
                    emotion_memory,
                    session_emotions,
                    pattern_memory,
                    goal_memory
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
    profile_memory,
    emotion_memory,
    session_emotions,
    pattern_memory,
    goal_memory
):
    event_type = event["type"]
    payload = event["payload"]

    if event_type == "system_started":
        console.print("[green]Event:[/green] system_started")

    elif event_type == "text_input":
        response = text_engine.process(payload)

        # ---------------------------------
        # SESSION EMOTION ANALYSIS
        # ---------------------------------
        if response == "__SESSION_EMOTION_ANALYSIS__":
            total = sum(session_emotions.values())
            if total == 0:
                console.print("[cyan]No emotional signals detected this session.[/cyan]")
            else:
                summary = "\n".join(
                    f"{e.capitalize()}: {c}"
                    for e, c in session_emotions.items()
                    if c > 0
                )
                console.print(f"[cyan]Session Emotional Summary ({total} entries):\n{summary}[/cyan]")

        # ---------------------------------
        # LONG-TERM EMOTION ANALYSIS
        # ---------------------------------
        elif response == "__EMOTION_ANALYSIS_REQUEST__":
            analysis = emotion_memory.analyze_recent(limit=20)
            if not analysis:
                console.print("[cyan]No emotional data available yet.[/cyan]")
            else:
                total = sum(analysis.values())
                summary = "\n".join(
                    f"{e.capitalize()}: {c}"
                    for e, c in analysis.items()
                )
                console.print(f"[cyan]Recent Emotional Summary ({total} entries):\n{summary}[/cyan]")

        # ---------------------------------
        # STABILITY SCORE
        # ---------------------------------
        elif response == "__STABILITY_SCORE_REQUEST__":
            analysis = emotion_memory.analyze_recent(limit=20)
            if not analysis:
                console.print("[cyan]No emotional data available yet.[/cyan]")
            else:
                stress = analysis.get("stress", 0)
                fatigue = analysis.get("fatigue", 0)
                positive = analysis.get("positive", 0)
                stability = positive - (stress + fatigue)
                console.print(f"[cyan]Emotional Stability Score: {stability}[/cyan]")

        # ---------------------------------
        # GOAL–EMOTION ALIGNMENT (Phase 28)
        # ---------------------------------
        elif response == "__GOAL_ALIGNMENT_REQUEST__":
            goals = goal_memory.list_goals()
            analysis = emotion_memory.analyze_recent(limit=20)

            if not goals:
                console.print("[cyan]No goals defined yet.[/cyan]")
            elif not analysis:
                console.print("[cyan]Insufficient emotional data to evaluate alignment.[/cyan]")
            else:
                stress = analysis.get("stress", 0)
                fatigue = analysis.get("fatigue", 0)
                positive = analysis.get("positive", 0)

                emotional_load = stress + fatigue

                if positive >= emotional_load:
                    console.print(
                        "[cyan]You appear emotionally aligned with your current goals.[/cyan]"
                    )
                else:
                    console.print(
                        "[cyan]Your emotional strain may be affecting goal alignment. "
                        "Consider adjusting pace or workload.[/cyan]"
                    )

        # ---------------------------------
        # PATTERN ANALYSIS
        # ---------------------------------
        elif "what have i been thinking about" in payload.lower():
            patterns = pattern_memory.analyze_recent(top_n=5)
            if not patterns:
                console.print("[cyan]No recurring themes detected yet.[/cyan]")
            else:
                summary = "\n".join(f"{w} ({c})" for w, c in patterns)
                console.print(f"[cyan]Recurring Themes:\n{summary}[/cyan]")

        # ---------------------------------
        # GOAL CREATION
        # ---------------------------------
        elif payload.lower().startswith("my goal is"):
            goal_text = payload[10:].strip()
            if goal_text:
                goal_memory.add_goal(goal_text)
                console.print(f"[cyan]Goal recorded: {goal_text}[/cyan]")
            else:
                console.print("[cyan]Please specify a valid goal.[/cyan]")

        # ---------------------------------
        # LIST GOALS
        # ---------------------------------
        elif "goal" in payload.lower() and "what" in payload.lower():
            goals = goal_memory.list_goals()
            if not goals:
                console.print("[cyan]No goals recorded yet.[/cyan]")
            else:
                summary = "\n".join(
                    f"{i+1}. {g['goal']}" for i, g in enumerate(goals)
                )
                console.print(f"[cyan]Your Goals:\n{summary}[/cyan]")

        # ---------------------------------
        # ADD PROGRESS NOTE
        # ---------------------------------
        elif payload.lower().startswith("add note to goal"):
            try:
                parts = payload.split(" ", 5)
                goal_index = int(parts[4]) - 1
                note = parts[5]
                success = goal_memory.add_progress_note(goal_index, note)
                if success:
                    console.print("[cyan]Progress note added.[/cyan]")
                else:
                    console.print("[cyan]Invalid goal index.[/cyan]")
            except Exception:
                console.print("[cyan]Format: add note to goal 1 Your note here[/cyan]")

        else:
            console.print(f"[cyan]{response}[/cyan]")

        # Emotion logging
        emotion = text_engine.detect_emotion(payload)
        if emotion:
            emotion_memory.log_emotion(emotion)
            if emotion in session_emotions:
                session_emotions[emotion] += 1

        pattern_memory.log_text(payload)

        extracted_name = text_engine.extract_name(payload)
        if extracted_name:
            profile_memory.update("name", extracted_name)
            text_engine.update_profile("name", extracted_name)

        interaction_logger.log(
            user_input=payload,
            system_response=response,
            version=identity["version"]
        )