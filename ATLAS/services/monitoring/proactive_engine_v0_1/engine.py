import json
import os
import time
import threading
from datetime import datetime

from services.monitoring.system_awareness_v0_1.awareness import system_awareness

_REMINDERS_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "memory", "structured", "reminders.json"
))


class ProactiveEngine:
    """
    Background engine that polls for trigger conditions every CHECK_INTERVAL seconds.
    On trigger: calls on_trigger_callback(message) — the voice runtime layer handles
    the chime + listen window and only speaks if the user responds.
    """

    CHECK_INTERVAL = 30
    FOCUS_DURATION_THRESHOLD_SECONDS = 90 * 60
    BATTERY_LOW_THRESHOLD = 15
    BATTERY_RESET_THRESHOLD = 25

    # Level 2 thresholds
    THRASHING_MIN_SWITCHES = 8
    THRASHING_WINDOW_SECONDS = 300
    THRASHING_DISTRACTION_RATIO_THRESHOLD = 0.4

    LATE_NIGHT_HOUR_START = 0
    LATE_NIGHT_HOUR_END = 5
    LATE_NIGHT_CHECK_COOLDOWN_SECONDS = 3600

    ENTERTAINMENT_SESSION_THRESHOLD_SECONDS = 2 * 60 * 60
    ENTERTAINMENT_PROCESSES = [
        "leagueclient.exe", "leagueclientux.exe", "valorant.exe",
        "spotify.exe", "steam.exe",
    ]

    DAILY_SUMMARY_HOUR = 21
    DAILY_SUMMARY_MINUTE_WINDOW = 5

    def __init__(self, on_trigger_callback):
        self._on_trigger = on_trigger_callback
        self._running = False
        self._thread = None
        self._focus_notified = False
        self._battery_notified = False
        self._last_focus_title = None
        # Level 2 cooldown state
        self._thrashing_already_notified = False
        self._late_night_last_notified = 0
        self._entertainment_already_notified = False
        self._entertainment_last_process = None
        self._daily_summary_fired_today = False
        self._daily_summary_last_date = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _is_muted(self) -> bool:
        mute_path = r"E:\Requirements\atlas_proactive_muted_until.json"
        if not os.path.exists(mute_path):
            return False
        try:
            with open(mute_path, "r") as f:
                data = json.load(f)
            return time.time() < data.get("mute_until", 0)
        except Exception:
            return False

    def _loop(self):
        while self._running:
            try:
                if not self._is_muted():
                    self._check_focus()
                    self._check_battery()
                    self._check_reminders()
                    self._check_thrashing()
                    self._check_late_night()
                    self._check_entertainment_session()
                    self._check_daily_summary()
            except Exception as e:
                print(f"[ProactiveEngine] Check error: {e}")
            time.sleep(self.CHECK_INTERVAL)

    def _check_focus(self):
        state = system_awareness.get_state()
        title = state.get("active_window_title")
        if title != self._last_focus_title:
            self._focus_notified = False
            self._last_focus_title = title
        if self._focus_notified:
            return
        duration = system_awareness.get_focus_duration_seconds()
        if duration >= self.FOCUS_DURATION_THRESHOLD_SECONDS:
            minutes = int(duration // 60)
            self._focus_notified = True
            self._on_trigger(
                f"You've been in {title} for {minutes} minutes. "
                f"Might be a good time for a short break."
            )

    def _check_battery(self):
        state = system_awareness.get_state()
        battery = state.get("battery_percent")
        plugged = state.get("battery_plugged")
        if battery is None:
            return
        if battery <= self.BATTERY_LOW_THRESHOLD and not plugged and not self._battery_notified:
            self._battery_notified = True
            self._on_trigger(
                f"Your battery is at {int(battery)} percent and not charging. "
                f"You might want to plug in."
            )
        if plugged or (battery is not None and battery >= self.BATTERY_RESET_THRESHOLD):
            self._battery_notified = False

    def _check_reminders(self):
        if not os.path.exists(_REMINDERS_PATH):
            return
        try:
            with open(_REMINDERS_PATH, "r", encoding="utf-8-sig") as f:
                reminders = json.load(f)
        except Exception:
            return

        now = datetime.now()
        changed = False
        for reminder in reminders:
            if reminder.get("notified"):
                continue
            due_at = reminder.get("due_at")
            if not due_at:
                continue
            try:
                due_time = datetime.fromisoformat(due_at)
            except Exception:
                continue
            if now >= due_time:
                reminder["notified"] = True
                changed = True
                self._on_trigger(f"Reminder: {reminder['text']}")

        if changed:
            try:
                with open(_REMINDERS_PATH, "w", encoding="utf-8") as f:
                    json.dump(reminders, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[ProactiveEngine] Failed to save reminder state: {e}")

    def _check_thrashing(self):
        summary = system_awareness.get_recent_switch_classification_summary(
            window_seconds=self.THRASHING_WINDOW_SECONDS
        )
        if summary["switch_count"] < self.THRASHING_MIN_SWITCHES:
            self._thrashing_already_notified = False
            return
        if summary["distraction_ratio"] < self.THRASHING_DISTRACTION_RATIO_THRESHOLD:
            self._thrashing_already_notified = False
            return
        if self._thrashing_already_notified:
            return
        self._thrashing_already_notified = True
        self._on_trigger(
            f"You've switched apps {summary['switch_count']} times in the last 5 minutes, "
            f"and a lot of it looks like distraction. Want to refocus?"
        )

    def _check_late_night(self):
        now = datetime.now()
        if not (self.LATE_NIGHT_HOUR_START <= now.hour < self.LATE_NIGHT_HOUR_END):
            return
        if time.time() - self._late_night_last_notified < self.LATE_NIGHT_CHECK_COOLDOWN_SECONDS:
            return
        self._late_night_last_notified = time.time()
        self._on_trigger(f"It's {now.strftime('%I:%M %p')}. Still up late — everything okay?")

    def _check_entertainment_session(self):
        state = system_awareness.get_state()
        process = (state.get("active_process_name") or "").lower()
        title = (state.get("active_window_title") or "").lower()

        is_entertainment = (
            any(p in process for p in self.ENTERTAINMENT_PROCESSES)
            or "netflix" in title
            or "youtube" in title
        )

        if not is_entertainment:
            self._entertainment_already_notified = False
            self._entertainment_last_process = None
            return

        if process != self._entertainment_last_process:
            self._entertainment_already_notified = False
            self._entertainment_last_process = process

        if self._entertainment_already_notified:
            return

        duration = system_awareness.get_focus_duration_seconds()
        if duration >= self.ENTERTAINMENT_SESSION_THRESHOLD_SECONDS:
            minutes = int(duration // 60)
            self._entertainment_already_notified = True
            self._on_trigger(
                f"You've been on {state.get('active_window_title')} for {minutes} minutes. Just checking in."
            )

    def _check_daily_summary(self):
        from services.monitoring.system_awareness_v0_1.history_logger import history_logger as hl

        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        if self._daily_summary_last_date != today_str:
            self._daily_summary_fired_today = False
            self._daily_summary_last_date = today_str

        if self._daily_summary_fired_today:
            return
        if now.hour != self.DAILY_SUMMARY_HOUR or now.minute > self.DAILY_SUMMARY_MINUTE_WINDOW:
            return

        totals = hl.get_today_summary()
        filtered = {k: v for k, v in totals.items() if v >= 60}
        if not filtered:
            return

        sorted_apps = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:3]
        parts = [f"{proc} for {int(sec // 60)} minutes" for proc, sec in sorted_apps]
        self._daily_summary_fired_today = True
        self._on_trigger("Here's your day so far: " + ", ".join(parts) + ".")
