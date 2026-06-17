import json
import os
import requests
from datetime import datetime

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
        reminders = _load_reminders()
        reminders.append({"text": text.strip(), "created_at": datetime.now().isoformat()})
        _save_reminders(reminders)
        return f"Reminder set: {text.strip()}."
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
