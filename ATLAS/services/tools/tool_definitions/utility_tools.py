import json
import os
import re
import requests
import parsedatetime
from datetime import datetime

_cal = parsedatetime.Calendar()

_NUM_WORDS = (
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|fifteen|twenty|thirty|forty|fifty|sixty|"
    r"a|an|half)"
)
_TIME_PHRASE_PATTERNS = [
    # "at 2:37pm", "at 2.37pm", "at 5pm", "at 14:00" — colon, period, or no separator
    r'\bat \d{1,2}[:.]\d{2}\s*(am|pm)?\b',
    r'\bat \d{1,2}\s*(am|pm)\b',
    rf'\bin {_NUM_WORDS}\s*(minute|minutes|min|mins|hour|hours|hr|hrs|day|days)\b',
    r'\btonight\b',
    r'\btoday\b',
    r'\btomorrow\b',
    r'\bnext\s+(week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
    r'\bon\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
]


def _normalize_time_separators(text: str) -> str:
    """Converts period-separated times like '2.37pm' to '2:37pm' so parsedatetime can parse them."""
    return re.sub(r'\b(\d{1,2})\.(\d{2})\s*(am|pm)\b', r'\1:\2\3', text, flags=re.IGNORECASE)


def _parse_due_time_and_clean(text: str):
    """
    Parses a due time from natural language and returns (due_time_or_None, cleaned_text).
    cleaned_text has the time phrase stripped so stored reminders read naturally
    (e.g. "call mom at 5pm" → due=5PM, text="call mom").
    Normalizes period-separated times (2.37pm → 2:37pm) before parsing.
    """
    normalized = _normalize_time_separators(text)
    time_struct, parse_status = _cal.parseDT(normalized, sourceTime=datetime.now())
    if parse_status == 0:
        return None, text

    cleaned = text  # strip from original (not normalized) for natural display
    for pattern in _TIME_PHRASE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(".,!? ")
    return time_struct, cleaned if cleaned else text

_REMINDERS_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "memory", "structured", "reminders.json"
))


def _get_time():
    return f"The time is {datetime.now().strftime('%I:%M %p')}."


def _get_date():
    return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."


def _wmo_code_to_description(code: int) -> str:
    mapping = {
        0: "clear sky",
        1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "icy fog",
        51: "light drizzle", 53: "moderate drizzle", 55: "heavy drizzle",
        61: "light rain", 63: "moderate rain", 65: "heavy rain",
        71: "light snow", 73: "moderate snow", 75: "heavy snow",
        80: "light showers", 81: "moderate showers", 82: "heavy showers",
        95: "thunderstorm",
    }
    return mapping.get(code, f"weather code {code}")


def _fetch_weather(city: str) -> str:
    try:
        geo_resp = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1",
            timeout=5
        ).json()
        results = geo_resp.get("results")
        if not results:
            return f"I couldn't find a city called {city}."
        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
        name = results[0]["name"]
        country = results[0].get("country", "")

        wx_resp = requests.get(
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current_weather=true",
            timeout=5
        ).json()
        cw = wx_resp.get("current_weather", {})
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        condition = _wmo_code_to_description(cw.get("weathercode", 0))
        return (
            f"Weather in {name}, {country}: {condition}. "
            f"Temperature {temp} degrees Celsius, wind speed {wind} kilometres per hour."
        )
    except requests.exceptions.ConnectionError:
        return "No internet connection. I can't fetch weather right now."
    except Exception as e:
        return f"Weather lookup failed: {e}"


def make_weather_handler(stt, tts):
    def _weather(arg=None):
        city = arg.strip() if arg and arg.strip() else None
        if not city:
            tts.speak("Which city?")
            city = stt.listen()
            if not city or not city.strip():
                return "I didn't catch a city name. Please try again."
        return _fetch_weather(city.strip())
    return _weather


def _load_reminders():
    if not os.path.exists(_REMINDERS_PATH):
        return []
    with open(_REMINDERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_reminders(data):
    os.makedirs(os.path.dirname(_REMINDERS_PATH), exist_ok=True)
    with open(_REMINDERS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def make_set_reminder_handler(stt, tts):
    def _set_reminder(arg=None):
        text = arg.strip() if arg and arg.strip() else None
        if not text:
            tts.speak("What should I remind you about?")
            text = stt.listen()
            if not text or not text.strip():
                return "I didn't catch the reminder. Please try again."
        due_time, clean_text = _parse_due_time_and_clean(text.strip())
        reminder = {
            "text": clean_text,
            "created_at": datetime.now().isoformat(),
            "due_at": due_time.isoformat() if due_time else None,
            "notified": False,
        }
        reminders = _load_reminders()
        reminders.append(reminder)
        _save_reminders(reminders)
        if due_time:
            due_str = due_time.strftime("%I:%M %p").lstrip("0")
            return f"Reminder set: {clean_text}. I'll remind you at {due_str}."
        return f"Reminder set: {clean_text}."
    return _set_reminder


def _list_reminders():
    reminders = _load_reminders()
    if not reminders:
        return "You have no reminders."
    parts = [f"{i + 1}: {r['text']}" for i, r in enumerate(reminders)]
    return "Your reminders: " + ". ".join(parts) + "."


def register_all(matcher, stt_engine, tts_engine):
    matcher.register([
        "what time is it", "what's the time", "current time", "tell me the time",
        "what is the time", "time right now", "time is it", "what time",
        "tell me the time", "give me the time",
    ], _get_time)
    matcher.register([
        "what's the date", "what day is it", "today's date", "current date",
        "what is the date", "what date is it", "date today", "tell me the date",
        "what is today", "today's day",
    ], _get_date)
    # "weather in X" must come before generic "weather" patterns so city is extracted
    matcher.register(["weather in"], make_weather_handler(stt_engine, tts_engine), needs_arg=True)
    matcher.register([
        "what's the weather", "weather today", "how's the weather", "weather",
        "what is the weather", "tell me the weather", "weather outside",
        "how is the weather", "weather forecast",
    ], make_weather_handler(stt_engine, tts_engine))
    matcher.register([
        "remind me to", "remind me about", "remind me that",
    ], make_set_reminder_handler(stt_engine, tts_engine), needs_arg=True)
    matcher.register([
        "set a reminder", "add a reminder", "create a reminder", "new reminder",
    ], make_set_reminder_handler(stt_engine, tts_engine))
    matcher.register([
        "what are my reminders", "list reminders", "show reminders", "my reminders",
        "read my reminders", "what reminders do i have", "do i have any reminders",
    ], _list_reminders)
