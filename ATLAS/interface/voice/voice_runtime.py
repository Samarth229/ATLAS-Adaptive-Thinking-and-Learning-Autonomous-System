import sys
import os
import time
import threading
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from rich.console import Console

_GUI_LOG_PATH = r"E:\Requirements\atlas_gui_conversation_log.json"
_GUI_NOTIFICATION_PATH = r"E:\Requirements\atlas_gui_last_notification.json"


def _atomic_write_json(path: str, data):
    """Write JSON atomically — temp file then os.replace() so readers never see a partial write."""
    dir_name = os.path.dirname(path)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=dir_name, delete=False, encoding="utf-8", suffix=".tmp"
    ) as tmp_f:
        json.dump(data, tmp_f)
        tmp_path = tmp_f.name
    os.replace(tmp_path, path)


def _log_for_gui(speaker: str, text: str):
    try:
        log = []
        if os.path.exists(_GUI_LOG_PATH):
            with open(_GUI_LOG_PATH, "r", encoding="utf-8-sig") as f:
                log = json.load(f)
        log.append({"speaker": speaker, "text": text, "timestamp": time.time()})
        log = log[-50:]
        _atomic_write_json(_GUI_LOG_PATH, log)
    except Exception as e:
        print(f"[GUI LOG ERROR] {e}")


def _write_notification_for_gui(message: str):
    try:
        with open(_GUI_NOTIFICATION_PATH, "w", encoding="utf-8") as f:
            json.dump({"message": message, "timestamp": time.time()}, f)
    except Exception:
        pass

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
from services.tools.tool_definitions import app_web_tools, system_tools, utility_tools, dev_tools, awareness_tools, vision_tools
from services.monitoring.system_awareness_v0_1.awareness import system_awareness
from services.monitoring.proactive_engine_v0_1.engine import ProactiveEngine
from services.monitoring.memory_extraction_v0_1.extractor import extract_facts_from_exchanges
from interface.voice.chime import play_chime

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
        self._proactive_engine = ProactiveEngine(on_trigger_callback=self._on_proactive_trigger)
        self._exchanges_since_last_extraction = 0
        self._EXTRACTION_INTERVAL = 10

    def _build_tool_matcher(self) -> ToolMatcher:
        matcher = ToolMatcher()
        # Registration order = priority order (first match wins).
        # Long specific-phrase tools before short/bare-keyword tools.
        # awareness_tools and utility_tools have multi-word phrases that must beat
        # bare keywords like "brave"/"chrome" in app_web_tools.
        awareness_tools.register_all(matcher)
        utility_tools.register_all(matcher, stt_engine=self._stt, tts_engine=self._tts)
        dev_tools.register_all(matcher)
        system_tools.register_all(matcher, stt_engine=self._stt, tts_engine=self._tts)
        vision_tools.register_all(matcher)
        app_web_tools.register_all(matcher)
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

    def _on_proactive_trigger(self, message: str):
        """Chime → 5-second listen window → speak only if user responded."""
        if not self._processing_lock.acquire(blocking=False):
            return  # busy with wake-word pipeline, skip this cycle
        try:
            play_chime()
            console.print("[bold yellow][Proactive] Chime played — waiting for response...[/bold yellow]")
            response_text = self._stt.listen()
            _write_notification_for_gui(message)
            if response_text and response_text.strip():
                console.print(f"[bold green]You (proactive):[/bold green] {response_text}")
                console.print(f"[bold cyan]ATLAS:[/bold cyan] {message}")
                self._tts.speak(message)
            else:
                console.print(f"[dim][Proactive] No response — staying quiet.[/dim]")
        except Exception as e:
            console.print(f"[red]Proactive trigger error: {e}[/red]")
        finally:
            self._processing_lock.release()

    def _maybe_run_extraction(self):
        self._exchanges_since_last_extraction += 1
        if self._exchanges_since_last_extraction >= self._EXTRACTION_INTERVAL:
            self._exchanges_since_last_extraction = 0
            self._run_extraction_async()

    def _run_extraction_async(self):
        def _do_extraction():
            try:
                if os.path.exists(_GUI_LOG_PATH):
                    with open(_GUI_LOG_PATH, "r", encoding="utf-8-sig") as f:
                        log = json.load(f)
                    recent = log[-20:]
                    result = extract_facts_from_exchanges(recent)
                    if result["error"]:
                        print(f"[MemoryExtraction] Error: {result['error']}")
                    elif result["new_facts_count"] > 0:
                        print(f"[MemoryExtraction] Learned {result['new_facts_count']} new fact(s).")
            except Exception as e:
                print(f"[MemoryExtraction] Background extraction error: {e}")
        threading.Thread(target=_do_extraction, daemon=True).start()

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
            _log_for_gui("user", text)

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
                _log_for_gui("atlas", combined)
                self._maybe_run_extraction()
                self._tts.speak(combined)
                return

            result = self._engine.process(text)
            response = result.get("text", "I have no response.")

            console.print(f"[bold cyan]ATLAS:[/bold cyan] {response}")
            _log_for_gui("atlas", response)
            self._maybe_run_extraction()
            self._tts.speak(response)

        except Exception as e:
            console.print(f"[red]Voice pipeline error: {e}[/red]")
        finally:
            self._processing_lock.release()

    def start(self):
        console.print("[bold yellow]ATLAS Voice Runtime Active[/bold yellow]")
        console.print("[dim]Say 'Hey Jarvis' to activate. Ctrl+C to exit.[/dim]")

        system_awareness.start()
        self._proactive_engine.start()
        self._tts.speak("ATLAS voice system online.")
        self._wakeword.start_listening(self._on_wake_word)

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self._wakeword.stop()
            system_awareness.stop()
            self._proactive_engine.stop()
            console.print("\n[bold red]Voice runtime shut down.[/bold red]")
