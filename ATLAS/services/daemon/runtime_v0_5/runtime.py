import time
import threading
from rich.console import Console

from services.daemon.event_bus import EventBus
from core.atlas_engine_v0_2 import AtlasEngineV0_2

from cognition.intent_engine_v0_1.intent import IntentEngineV0_1
from cognition.reasoning.text_engine_v0_1.engine import TextEngineV0_1
from cognition.state.state_engine_v0_1.state import CognitiveStateEngineV0_1

from cognition.models.adapters.rule_based_adapter_v0_1 import RuleBasedAdapterV0_1

from memory.engine.interaction_loader_v0_1.loader import InteractionLoaderV0_1
from memory.engine.profile_memory_v0_1.profile import ProfileMemoryV0_1
from memory.engine.goal_memory_v0_1.goal import GoalMemoryV0_1
from memory.engine.emotion_memory_v0_1.emotion_logger import EmotionMemoryV0_1
from cognition.models.router.model_router_v0_1 import ModelRouterV0_1


RUNTIME_VERSION = "0.5"
console = Console()
shutdown_event = threading.Event()


def start_runtime(identity):

    console.print(
        f"[bold yellow]A.T.L.A.S entering interactive runtime (v{RUNTIME_VERSION})...[/bold yellow]"
    )

    event_bus = EventBus()

    interaction_loader = InteractionLoaderV0_1()
    recent_history = interaction_loader.load_recent(limit=5)
    total_interactions = interaction_loader.total_interactions()

    profile_memory = ProfileMemoryV0_1()
    profile_data = profile_memory.load()

    goal_memory = GoalMemoryV0_1()
    emotion_memory = EmotionMemoryV0_1()

    session_emotions = {
        "stress": 0,
        "fatigue": 0,
        "positive": 0
    }

    intent_engine = IntentEngineV0_1()

    state_engine = CognitiveStateEngineV0_1(
        emotion_memory,
        goal_memory
    )

    text_engine = TextEngineV0_1(
        identity,
        recent_history,
        profile_data,
        total_interactions,
        state_engine.build_state().get("dominant_emotion")
    )

    rule_model = RuleBasedAdapterV0_1(text_engine=text_engine)
    model_router = ModelRouterV0_1(default_model=rule_model)
    model_router.register_model("rule", rule_model)

    engine = AtlasEngineV0_2(
        model=model_router,
        text_engine=text_engine,
        intent_engine=intent_engine,
        identity=identity,
        goal_memory=goal_memory,
        session_emotions=session_emotions,
        state_engine=state_engine,
        emotion_memory=emotion_memory
    )

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
                handle_event(event, engine)

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


def handle_event(event, engine):

    if event["type"] != "text_input":
        return

    payload = event["payload"]

    result = engine.process(payload)

    console.print(
        f"[dim]Detected intent: {result['intent']} (confidence: {result['confidence']})[/dim]"
    )

    console.print(f"[cyan]{result['text']}[/cyan]")