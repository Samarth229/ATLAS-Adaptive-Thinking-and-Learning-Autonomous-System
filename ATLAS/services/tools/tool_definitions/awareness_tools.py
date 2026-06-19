import re
from services.monitoring.system_awareness_v0_1.awareness import system_awareness
from services.monitoring.system_awareness_v0_1.history_logger import history_logger

# Trailing words that get included in arg extraction but should be stripped.
# Allow optional punctuation/whitespace around the qualifier (STT often adds ? or .)
_TRAILING_QUALIFIERS = re.compile(
    r'[\s?!.,]+(today|this week|this month|right now|so far|in total|this session)[\s?!.,]*$',
    flags=re.IGNORECASE
)


def _what_app(arg=None):
    state = system_awareness.get_state()
    title = state.get("active_window_title")
    if not title:
        return "I couldn't detect the active window."
    return f"You're currently in {title}."


def _focus_duration(arg=None):
    state = system_awareness.get_state()
    title = state.get("active_window_title") or "this window"
    seconds = system_awareness.get_focus_duration_seconds()
    minutes = int(seconds // 60)
    if minutes < 1:
        return f"You've had {title} open for less than a minute."
    elif minutes < 60:
        return f"You've had {title} open for {minutes} minute{'s' if minutes != 1 else ''}."
    else:
        hours = minutes // 60
        remainder = minutes % 60
        return f"You've had {title} open for {hours} hour{'s' if hours != 1 else ''} and {remainder} minutes."


def _running_apps(arg=None):
    apps = system_awareness.get_running_apps(limit=8)
    if not apps:
        return "I couldn't detect any running apps."
    return f"You currently have these running: {', '.join(apps)}."


def _system_resources(arg=None):
    state = system_awareness.get_state()
    cpu = state.get("cpu_percent", 0.0)
    ram = state.get("ram_percent", 0.0)
    battery = state.get("battery_percent")
    plugged = state.get("battery_plugged")

    parts = [f"CPU is at {cpu:.0f} percent", f"RAM is at {ram:.0f} percent"]
    if battery is not None:
        status = "and charging" if plugged else "and not charging"
        parts.append(f"battery is at {battery:.0f} percent {status}")
    return ", ".join(parts) + "."


def _time_spent_on_app(arg=None):
    if not arg or not arg.strip():
        return "Which app would you like to know about?"
    # Strip trailing punctuation first, then trailing time qualifiers
    clean_arg = arg.strip().rstrip("?!.,").strip()
    clean_arg = _TRAILING_QUALIFIERS.sub("", clean_arg).strip().rstrip("?!.,").strip()
    seconds = history_logger.get_time_for_app(clean_arg)
    name = clean_arg
    if seconds < 1:
        return f"I don't have any recorded time for {name} today."
    minutes = int(seconds // 60)
    if minutes < 1:
        return f"You've spent less than a minute on {name} today."
    elif minutes < 60:
        return f"You've spent {minutes} minute{'s' if minutes != 1 else ''} on {name} today."
    else:
        hours = minutes // 60
        remainder = minutes % 60
        return f"You've spent {hours} hour{'s' if hours != 1 else ''} and {remainder} minutes on {name} today."


def _most_used_today(arg=None):
    totals = history_logger.get_today_summary()
    filtered = {k: v for k, v in totals.items() if v >= 60}
    if not filtered:
        return "I don't have enough data yet today. Keep using your PC and ask again later."
    sorted_apps = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:5]
    parts = []
    for proc, seconds in sorted_apps:
        minutes = int(seconds // 60)
        parts.append(f"{proc} for {minutes} minute{'s' if minutes != 1 else ''}")
    return "Today you spent the most time on: " + ", ".join(parts) + "."


def register_all(matcher):
    matcher.register([
        "what app am i in", "what am i doing", "what window is open",
        "what app is open", "which app am i using", "current app",
        "what's the active window", "what are you looking at",
        "what app is focused", "what's open",
    ], _what_app)

    matcher.register([
        # Full phrases
        "how long have i been in this", "how long have i been here",
        "how long have i been using this", "focus duration",
        "how long was i in this app", "how long have i had this open",
        "how long in this window", "how long on this",
        "how long have i been on this", "time spent here",
        # Short/incomplete phrases — these are the ones that fall to the LLM
        # because intent engine catches "how" + "been" and routes to emotion_summary
        "how long have i been", "how long was i", "how long have i",
        "how long in this", "how long on this app",
    ], _focus_duration)

    matcher.register([
        "what's running on my pc", "what apps are running", "what's open right now",
        "list running apps", "what programs are running", "what's running",
        "what processes are running",
    ], _running_apps)

    matcher.register([
        "what's my cpu usage", "what's my ram usage", "system resources",
        "how's my system doing", "what's my battery", "cpu and ram",
        "check system performance", "how's my pc doing",
        "what's my cpu", "what's my ram", "my cpu", "my ram",
        "cpu usage", "ram usage", "check my cpu", "check my ram",
        "how much cpu", "how much ram", "system status",
        "what's my battery percentage", "battery level", "battery status",
        "how's my battery", "what's my battery at", "check battery",
    ], _system_resources)

    matcher.register([
        "how much time did i spend on", "how much time have i spent on",
        "time spent on", "how long did i spend on", "how long have i spent on",
        "how much time on",
    ], _time_spent_on_app, needs_arg=True)

    matcher.register([
        "what have i used most today", "what did i use most today",
        "most used app today", "what app did i use most",
        "show my activity today", "what was i doing most today",
        "activity summary", "today's activity",
        "which app have i used today", "which app have i used most today",
        "which is the most used app today", "what's my most used app",
        "what app have i used the most", "which app did i use the most",
        "what have i used today", "what apps have i used today",
    ], _most_used_today)
