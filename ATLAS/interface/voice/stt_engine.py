import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

_WHISPER_CACHE = r"E:\Requirements\huggingface\hub"


class STTEngine:

    def __init__(self, model_size="medium", record_seconds=6, sample_rate=16000):
        self.sample_rate = sample_rate
        self.record_seconds = record_seconds
        self._model = None
        self._model_size = model_size

    def _load_model(self):
        if self._model is not None:
            return
        try:
            self._model = WhisperModel(
                self._model_size,
                device="cuda",
                compute_type="float16",
                download_root=_WHISPER_CACHE
            )
            print(f"[STT] Whisper {self._model_size} loaded on CUDA.")
        except Exception as e:
            print(f"[STT] CUDA unavailable ({e}), falling back to CPU.")
            self._model = WhisperModel(
                self._model_size,
                device="cpu",
                compute_type="int8",
                download_root=_WHISPER_CACHE
            )
            print(f"[STT] Whisper {self._model_size} loaded on CPU.")

    def listen(self) -> str:
        self._load_model()
        print(f"[STT] Recording for {self.record_seconds}s...")
        audio = sd.rec(
            int(self.record_seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32"
        )
        sd.wait()
        audio_flat = audio.flatten()

        segments, info = self._model.transcribe(
            audio_flat,
            language=None,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        text = " ".join(seg.text.strip() for seg in segments).strip()
        if text:
            print(f"[STT] Transcribed ({info.language}): {text}")
        else:
            print("[STT] No speech detected.")
        return text
