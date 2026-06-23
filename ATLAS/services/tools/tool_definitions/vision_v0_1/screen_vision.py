import base64
import io
import requests
import mss
import numpy as np
from PIL import Image

from services.monitoring.system_awareness_v0_1.awareness import system_awareness


_OLLAMA_URL = "http://localhost:11434/api/generate"
_MODEL = "llava"

_KNOWN_DRM_SERVICES = [
    "netflix", "prime video", "amazon prime", "hotstar", "disney+",
    "hulu", "hbo max", "apple tv", "youtube premium movies", "spotify",
]


def _is_mostly_black(img: Image.Image, threshold: int = 10, black_ratio: float = 0.95) -> bool:
    """Returns True if ≥95% of pixels are near-black — strong indicator of DRM screenshot blocking."""
    img_array = np.array(img.resize((100, 100)).convert("L"))
    return (np.sum(img_array < threshold) / img_array.size) >= black_ratio


def ask_about_screen(question: str = None) -> str:
    """
    Captures the current screen and asks LLaVA a question about it.
    No image is ever written to disk — capture, encode, and send all happen in memory.
    Detects DRM-protected black screens before calling the vision model.
    """
    if not question or not question.strip():
        question = (
            "Describe what's currently shown on this screen. "
            "Look carefully for specific identifying details like application names, "
            "website names, file names, or text visible in the interface before describing "
            "what kind of application or website this is. Be specific rather than general."
        )
    else:
        question = (
            f"{question} "
            "Before answering, look carefully for specific identifying text, logos, "
            "or labels visible in the image to make sure your answer is accurate."
        )

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    except Exception as e:
        return f"I couldn't capture the screen: {e}"

    # DRM black-screen check — skip vision model entirely if triggered
    if _is_mostly_black(img):
        state = system_awareness.get_state()
        title = (state.get("active_window_title") or "").lower()
        matched = next((s for s in _KNOWN_DRM_SERVICES if s in title), None)
        if matched:
            return (
                f"It looks like you're watching something on {matched.title()}, "
                f"but I can't actually see the video content — that's protected from screenshots."
            )
        return (
            "I'm seeing a mostly black screen, which usually means the content is "
            "protected from screenshots, like a streaming video. I can't see what's actually playing."
        )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    try:
        response = requests.post(
            _OLLAMA_URL,
            json={
                "model": _MODEL,
                "prompt": question,
                "images": [image_b64],
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        answer = response.json().get("response", "").strip()
        return answer if answer else "I looked at the screen but couldn't come up with a description."

    except requests.exceptions.ConnectionError:
        return "I couldn't reach the local AI model. Make sure Ollama is running."
    except requests.exceptions.Timeout:
        return "That took too long to analyze. Try again or ask something more specific."
    except Exception as e:
        return f"Something went wrong analyzing the screen: {e}"
