import os
import sounddevice as sd
import soundfile as sf

_PRIMARY_MODEL = "tts_models/en/vctk/vits"
_PRIMARY_SPEAKER = "p326"
_FALLBACK_MODEL = "tts_models/en/ljspeech/glow-tts"

# Temp audio outside the repo — never committed
_TEMP_WAV = r"E:\Requirements\temp_audio.wav"


class TTSEngine:

    def __init__(self):
        self._tts = None
        self._speaker = None

    def _load_model(self):
        if self._tts is not None:
            return
        from TTS.api import TTS
        import torch
        use_gpu = torch.cuda.is_available()

        # Primary: male voice (requires eSpeak-ng installed on system)
        try:
            tts = TTS(_PRIMARY_MODEL)
            if use_gpu:
                tts = tts.to("cuda")
            self._tts = tts
            self._speaker = _PRIMARY_SPEAKER
            print("[TTS] VCTK VITS (male p326) loaded.")
            return
        except Exception as e:
            print(f"[TTS] Primary model failed ({e}). Falling back to GlowTTS.")

        # Fallback: no eSpeak needed
        tts = TTS(_FALLBACK_MODEL)
        if use_gpu:
            tts = tts.to("cuda")
        self._tts = tts
        self._speaker = None
        print("[TTS] LJSpeech GlowTTS (fallback) loaded.")

    def speak(self, text: str):
        if not text or not text.strip():
            return
        self._load_model()
        try:
            kwargs = {"text": text, "file_path": _TEMP_WAV}
            if self._speaker:
                kwargs["speaker"] = self._speaker
            self._tts.tts_to_file(**kwargs)
            data, samplerate = sf.read(_TEMP_WAV)
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            print(f"[TTS] Speak error: {e}")
