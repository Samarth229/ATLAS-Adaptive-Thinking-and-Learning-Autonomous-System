import os
import json
import glob
import statistics
from datetime import datetime
from collections import defaultdict


_ACTIVITY_HISTORY_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "memory", "structured", "activity_history"
))
_MIN_DAYS_FOR_RELIABLE_STATS = 14


class PatternStatsEngine:
    """
    Reads accumulated activity_history JSONL files and computes behavioral statistics.
    Degrades gracefully with sparse data — flags results as low-confidence until
    enough history exists.
    """

    def __init__(self, history_dir=None):
        self._history_dir = history_dir or _ACTIVITY_HISTORY_DIR

    def _load_all_days(self, max_days=90):
        if not os.path.exists(self._history_dir):
            return []
        files = glob.glob(os.path.join(self._history_dir, "*.jsonl"))
        files.sort(reverse=True)
        files = files[:max_days]
        all_records = []
        for filepath in files:
            date_str = os.path.basename(filepath).replace(".jsonl", "")
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        record["_date"] = date_str
                        all_records.append(record)
            except Exception as e:
                print(f"[PatternStats] Error reading {filepath}: {e}")
        return all_records

    def get_data_coverage(self) -> dict:
        if not os.path.exists(self._history_dir):
            return {"days_available": 0, "reliable": False}
        files = glob.glob(os.path.join(self._history_dir, "*.jsonl"))
        days_available = len(files)
        return {
            "days_available": days_available,
            "reliable": days_available >= _MIN_DAYS_FOR_RELIABLE_STATS,
        }

    def get_typical_session_length(self, process_name: str) -> dict:
        records = self._load_all_days()
        process_lower = process_name.lower()
        durations = [
            r["duration_seconds"] for r in records
            if process_lower in (r.get("process") or "").lower()
            and r.get("duration_seconds", 0) >= 30
        ]
        if not durations:
            return {
                "process": process_name,
                "median_seconds": None,
                "mean_seconds": None,
                "session_count": 0,
                "reliable": False,
            }
        coverage = self.get_data_coverage()
        return {
            "process": process_name,
            "median_seconds": statistics.median(durations),
            "mean_seconds": statistics.mean(durations),
            "session_count": len(durations),
            "reliable": coverage["reliable"] and len(durations) >= 5,
        }

    def get_typical_active_hours(self) -> dict:
        records = self._load_all_days()
        weekday_hours = defaultdict(int)
        weekend_hours = defaultdict(int)
        for r in records:
            start_str = r.get("start")
            if not start_str:
                continue
            try:
                start_dt = datetime.fromisoformat(start_str)
            except Exception:
                continue
            hour = start_dt.hour
            duration = r.get("duration_seconds", 0)
            if start_dt.weekday() >= 5:
                weekend_hours[hour] += duration
            else:
                weekday_hours[hour] += duration

        def top_hours(hour_dict, n=5):
            return [h for h, _ in sorted(hour_dict.items(), key=lambda x: x[1], reverse=True)[:n]]

        coverage = self.get_data_coverage()
        return {
            "weekday_most_active_hours": top_hours(weekday_hours),
            "weekend_most_active_hours": top_hours(weekend_hours),
            "reliable": coverage["reliable"],
        }

    def get_last_active_time_before_late_night(self) -> dict:
        records = self._load_all_days()
        late_session_end_hours = []
        for r in records:
            end_str = r.get("end")
            if not end_str:
                continue
            try:
                end_dt = datetime.fromisoformat(end_str)
            except Exception:
                continue
            hour = end_dt.hour
            if hour >= 21 or hour < 6:
                normalized_hour = hour if hour < 6 else hour - 24
                late_session_end_hours.append(normalized_hour)
        coverage = self.get_data_coverage()
        if not late_session_end_hours:
            return {"typical_sleep_hour": None, "reliable": False, "sample_count": 0}
        return {
            "typical_sleep_hour_estimate": statistics.median(late_session_end_hours),
            "sample_count": len(late_session_end_hours),
            "reliable": coverage["reliable"] and len(late_session_end_hours) >= 10,
        }

    def get_full_profile_summary(self) -> dict:
        coverage = self.get_data_coverage()
        return {
            "data_coverage": coverage,
            "active_hours": self.get_typical_active_hours(),
            "late_night_pattern": self.get_last_active_time_before_late_night(),
            "note": (
                f"Statistics improve in reliability as more days of data accumulate. "
                f"Currently {coverage['days_available']} day(s) available; "
                f"{_MIN_DAYS_FOR_RELIABLE_STATS}+ recommended for reliable patterns."
            ),
        }


pattern_stats = PatternStatsEngine()
