import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from rich.console import Console

from interface.voice.stt_engine import STTEngine
from interface.voice.tts_engine import TTSEngine
from interface.voice.wake_word import WakeWordDetector

from services.daemon.event_bus import EventBus
from core.atlas_engine_v0_2 import AtlasEngineV0_2

from cognition.intent_engine_v0_1.intent import IntentEngineV0_1
from cognition.reasoning.text_engine_v0_1.engine import TextEngineV0_1
from cognition.state.state_engine_v0_1.state import CognitiveStateEngineV0_1

from cognition.models.adapters.rule_based_adapter_v0_1 import RuleBasedAdapterV0_1
from cognition.models.adapters.ollama_adapter_v0_1 import OllamaAdapterV0_1
from cognition.models.router.model_router_v0_1 import ModelRouterV0_1

from memory.engine.interaction_loader_v0_1.loader import InteractionLoaderV0_1
from memory.engine.profile_memory_v0_1.profile import ProfileMemoryV0_1
from memory.engine.goal_memory_v0_1.goal import GoalMemoryV0_1
from memory.engine.emotion_memory_v0_1.emotion_logger import EmotionMemoryV0_1

from services.tools.tool_matcher_v0_1.matcher import ToolMatcher
from services.tools.tool_definitions import app_web_tools, system_tools, utility_tools, dev_tools

console = Console()


class VoiceRuntime:

    def __init__(self, system_context: dict):
        self.identity = system_context["identity"]
        self._processing_lock = threading.Lock()
        self._engine = self._build_engine()
        self._stt = STTEngine(model_size="medium", record_seconds=7)
        self._tts = TTSEngine()
        self._wakeword = WakeWordDetector(sensitivity=0.5)
        self._tool_matcher = self._build_tool_matcher()

    def _build_tool_matcher(self) -> ToolMatcher:
        matcher = ToolMatcher()
        # dev_tools first — specific project keywords must not be caught by generic app_web patterns
        dev_tools.register_all(matcher)
        app_web_tools.register_all(matcher)
        system_tools.register_all(matcher, stt_engine=self._stt, tts_engine=self._tts)
        utility_tools.register_all(matcher, stt_engine=self._stt, tts_engine=self._tts)
        return matcher

    def _build_engine(self) -> AtlasEngineV0_2:
        interaction_loader = InteractionLoaderV0_1()
        recent_history = interaction_loader.load_recent(limit=5)
        total_interactions = interaction_loader.total_interactions()

        profile_memory = ProfileMemoryV0_1()
        profile_data = profile_memory.load()

        goal_memory = GoalMemoryV0_1()
        emotion_memory = EmotionMemoryV0_1()

        session_emotions = {"stress": 0, "fatigue": 0, "positive": 0}

        intent_engine = IntentEngineV0_1()

        state_engine = CognitiveStateEngineV0_1(emotion_memory, goal_memory)

        text_engine = TextEngineV0_1(
            self.identity,
            recent_history,
            profile_data,
            total_interactions,
            state_engine.build_state().get("dominant_emotion")
        )

        rule_model = RuleBasedAdapterV0_1(text_engine=text_engine)

        adapters = {
            "mistral": OllamaAdapterV0_1("mistral"),
            "phi": OllamaAdapterV0_1("phi3"),
            "deepseek": OllamaAdapterV0_1("deepseek-coder:6.7b"),
            "llama": OllamaAdapterV0_1("llama3.1:8b"),
        }

        model_router = ModelRouterV0_1(adapters)
        model_router.adapters["fallback"] = rule_model

        return AtlasEngineV0_2(
            model=model_router,
            text_engine=text_engine,
            intent_engine=intent_engine,
            identity=self.identity,
            goal_memory=goal_memory,
            session_emotions=session_emotions,
            state_engine=state_engine,
            emotion_memory=emotion_memory
        )

    def _on_wake_word(self):
        if not self._processing_lock.acquire(blocking=False):
            return
        try:
            self._tts.speak("Listening.")
            time.sleep(0.3)
            text = self._stt.listen()

            if not text:
                self._tts.speak("I did not catch that.")
                return

            console.print(f"[bold green]You:[/bold green] {text}")

            matches = self._tool_matcher.match_all(text)
            if matches:
                responses = []
                for match in matches:
                    try:
                        if match["arg"] is not None:
                            response = match["handler"](match["arg"])
                        else:
                            response = match["handler"]()
                    except Exception as e:
                        response = f"Sorry, I couldn't do that. {e}"
                    responses.append(response)
                combined = " ".join(responses)
                console.print(f"[bold cyan]ATLAS:[/bold cyan] {combined}")
                self._tts.speak(combined)
                return

            result = self._engine.process(text)
            response = result.get("text", "I have no response.")

            console.print(f"[bold cyan]ATLAS:[/bold cyan] {response}")
            self._tts.speak(response)

        except Exception as e:
            console.print(f"[red]Voice pipeline error: {e}[/red]")
        finally:
            self._processing_lock.release()

    def start(self):
        console.print("[bold yellow]ATLAS Voice Runtime Active[/bold yellow]")
        console.print("[dim]Say 'Hey Jarvis' to activate. Ctrl+C to exit.[/dim]")

        self._tts.speak("ATLAS voice system online.")
        self._wakeword.start_listening(self._on_wake_word)

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self._wakeword.stop()
            console.print("\n[bold red]Voice runtime shut down.[/bold red]")
