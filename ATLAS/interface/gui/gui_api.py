import json
import os
import time
from datetime import datetime

from services.monitoring.system_awareness_v0_1.awareness import system_awareness
from services.monitoring.system_awareness_v0_1.history_logger import history_logger
from services.monitoring.pattern_learning_v0_1.stats_engine import pattern_stats
from services.monitoring.memory_extraction_v0_1.extractor import extract_facts_from_exchanges, get_all_facts


_REMINDERS_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "memory", "structured", "reminders.json"
))
_PROACTIVE_MUTE_FLAG_PATH = r"E:\Requirements\atlas_proactive_muted_until.json"
_GUI_LOG_PATH = r"E:\Requirements\atlas_gui_conversation_log.json"
_GUI_NOTIFICATION_PATH = r"E:\Requirements\atlas_gui_last_notification.json"


class GuiApi:
    """
    Exposed to the JS frontend via pywebview's js_api.
    Every public method is callable from JS as window.pywebview.api.<method>(...)
    """

    def get_live_state(self):
        state = system_awareness.get_state()
        focus_duration = system_awareness.get_focus_duration_seconds()
        return {
            "active_window_title": state.get("active_window_title"),
            "active_process_name": state.get("active_process_name"),
            "focus_duration_minutes": round(focus_duration / 60, 1),
            "cpu_percent": state.get("cpu_percent"),
            "ram_percent": state.get("ram_percent"),
            "battery_percent": state.get("battery_percent"),
            "battery_plugged": state.get("battery_plugged"),
            "current_time": datetime.now().strftime("%H:%M"),
        }

    def get_today_usage(self):
        totals = history_logger.get_today_summary()
        filtered = {k: v for k, v in totals.items() if v >= 30}
        sorted_apps = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:6]
        max_seconds = sorted_apps[0][1] if sorted_apps else 1
        return [
            {
                "process": proc,
                "minutes": round(seconds / 60, 1),
                "percent_of_max": round((seconds / max_seconds) * 100),
            }
            for proc, seconds in sorted_apps
        ]

    def get_learning_progress(self):
        coverage = pattern_stats.get_data_coverage()
        return {
            "days_available": coverage["days_available"],
            "days_needed": 14,
            "reliable": coverage["reliable"],
            "percent": min(100, round((coverage["days_available"] / 14) * 100)),
        }

    def get_reminders(self):
        if not os.path.exists(_REMINDERS_PATH):
            return []
        try:
            with open(_REMINDERS_PATH, "r", encoding="utf-8-sig") as f:
                reminders = json.load(f)
            return [r for r in reminders if not r.get("notified", False)]
        except Exception:
            return []

    def dismiss_reminder(self, reminder_text):
        if not os.path.exists(_REMINDERS_PATH):
            return {"success": False}
        try:
            with open(_REMINDERS_PATH, "r", encoding="utf-8-sig") as f:
                reminders = json.load(f)
            for r in reminders:
                if r.get("text") == reminder_text:
                    r["notified"] = True
            with open(_REMINDERS_PATH, "w", encoding="utf-8") as f:
                json.dump(reminders, f, indent=2)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mute_proactive(self, minutes):
        mute_until = time.time() + (minutes * 60)
        try:
            os.makedirs(os.path.dirname(_PROACTIVE_MUTE_FLAG_PATH), exist_ok=True)
            with open(_PROACTIVE_MUTE_FLAG_PATH, "w") as f:
                json.dump({"mute_until": mute_until}, f)
            return {"success": True, "muted_until": mute_until}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_mute_status(self):
        if not os.path.exists(_PROACTIVE_MUTE_FLAG_PATH):
            return {"muted": False}
        try:
            with open(_PROACTIVE_MUTE_FLAG_PATH, "r") as f:
                data = json.load(f)
            mute_until = data.get("mute_until", 0)
            if time.time() < mute_until:
                remaining_minutes = round((mute_until - time.time()) / 60)
                return {"muted": True, "remaining_minutes": remaining_minutes}
            return {"muted": False}
        except Exception:
            return {"muted": False}

    def get_conversation_log(self):
        if not os.path.exists(_GUI_LOG_PATH):
            return []
        try:
            with open(_GUI_LOG_PATH, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception:
            return []

    def get_last_notification(self):
        if not os.path.exists(_GUI_NOTIFICATION_PATH):
            return None
        try:
            with open(_GUI_NOTIFICATION_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def clear_conversation_with_extraction(self):
        try:
            if os.path.exists(_GUI_LOG_PATH):
                with open(_GUI_LOG_PATH, "r", encoding="utf-8-sig") as f:
                    log = json.load(f)
            else:
                log = []
            result = extract_facts_from_exchanges(log)
            with open(_GUI_LOG_PATH, "w", encoding="utf-8") as f:
                json.dump([], f)
            return {
                "cleared": True,
                "facts_learned_before_clearing": result["new_facts_count"],
                "facts": result["facts"],
                "error": result["error"],
            }
        except Exception as e:
            return {"cleared": False, "error": str(e)}

    def get_extracted_facts(self):
        return get_all_facts()


gui_api = GuiApi()
