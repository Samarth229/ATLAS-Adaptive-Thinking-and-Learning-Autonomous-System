import io
import wave
import winsound
import numpy as np


def play_chime():
    """Plays a short two-tone notification chime via winsound (Windows audio API).
    Uses winsound instead of sounddevice to avoid device-sharing conflicts with TTS."""
    sample_rate = 22050
    duration = 0.18

    def tone(freq, dur):
        t = np.linspace(0, dur, int(sample_rate * dur), False)
        wave_data = np.sin(freq * 2 * np.pi * t) * 0.35
        fade = np.linspace(1.0, 0.0, len(wave_data))
        return (wave_data * fade * 32767).astype(np.int16)

    chime = np.concatenate([tone(880, duration), tone(1320, duration)])

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(chime.tobytes())

    winsound.PlaySound(buf.getvalue(), winsound.SND_MEMORY)
