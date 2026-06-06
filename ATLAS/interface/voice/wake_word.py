import threading
import numpy as np
import pyaudio
import openwakeword
from openwakeword.model import Model as OWWModel

_CHUNK = 1280       # 80ms @ 16kHz
_RATE = 16000
_FORMAT = pyaudio.paInt16
_CHANNELS = 1
_THRESHOLD = 0.5
_MODEL_DIR = r"E:\Requirements\openwakeword"


class WakeWordDetector:

    def __init__(self, sensitivity=_THRESHOLD):
        self.sensitivity = sensitivity
        self._running = False
        self._thread = None
        self._model = None

    def _load_model(self):
        self._model = OWWModel(
            wakeword_models=["hey_jarvis"],
            inference_framework="onnx"
        )
        print("[WakeWord] Model loaded: hey_jarvis (say 'Hey Jarvis' to activate ATLAS)")

    def start_listening(self, on_detected_callback):
        if self._running:
            return
        self._load_model()
        self._running = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            args=(on_detected_callback,),
            daemon=True
        )
        self._thread.start()
        print("[WakeWord] Listening in background...")

    def stop(self):
        self._running = False

    def _listen_loop(self, callback):
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=_FORMAT,
            channels=_CHANNELS,
            rate=_RATE,
            input=True,
            frames_per_buffer=_CHUNK
        )
        try:
            while self._running:
                try:
                    raw = stream.read(_CHUNK, exception_on_overflow=False)
                except OSError:
                    break
                audio = np.frombuffer(raw, dtype=np.int16)
                self._model.predict(audio)

                for name, score in self._model.prediction_buffer.items():
                    recent = list(score)[-1] if score else 0.0
                    if recent >= self.sensitivity:
                        print(f"[WakeWord] Detected '{name}' (score={recent:.2f})")
                        self._model.reset()
                        callback()
                        break
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
