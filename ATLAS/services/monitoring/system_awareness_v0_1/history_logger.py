import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[4]
_LOG_DIR = BASE_DIR / "memory" / "structured" / "activity_history"

# Maps spoken app names to process name substrings (lowercase)
_APP_NAME_ALIASES = {
    "vs code": "code",
    "visual studio code": "code",
    "vscode": "code",
    "chrome": "chrome",
    "brave": "brave",
    "league of legends": "league",
    "league": "league",
    "lol": "league",
    "discord": "discord",
    "spotify": "spotify",
    "steam": "steam",
    "notepad": "notepad",
    "file explorer": "explorer",
    "explorer": "explorer",
    "ollama": "ollama",
    "python": "python",
    "terminal": "windowsterminal",
    "windows terminal": "windowsterminal",
    "powershell": "powershell",
    "command prompt": "cmd",
    "youtube": "brave",   # usually watched in browser
    "vlc": "vlc",
    "obs": "obs64",
}


def resolve_app_alias(spoken_name: str) -> str:
    spoken_lower = spoken_name.lower().strip().rstrip("?!.,").strip()
    return _APP_NAME_ALIASES.get(spoken_lower, spoken_lower)


class HistoryLogger:
    """
    Logs app focus-switch events to a daily JSON Lines file.
    Each line: {"process": str, "title": str, "start": iso, "end": iso, "duration_seconds": float}
    """

    def __init__(self):
        os.makedirs(_LOG_DIR, exist_ok=True)
        self._lock = threading.Lock()
        self._current_process = None
        self._current_title = None
        self._segment_start = None

    def _today_path(self):
        return os.path.join(_LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.jsonl")

    def on_window_change(self, process_name, title):
        with self._lock:
            now = time.time()
            if self._current_process is not None and self._segment_start is not None:
                duration = now - self._segment_start
                if duration >= 1.0:
                    self._write_segment(
                        self._current_process, self._current_title,
                        self._segment_start, now, duration
                    )
            self._current_process = process_name
            self._current_title = title
            self._segment_start = now

    def _write_segment(self, process, title, start_ts, end_ts, duration):
        record = {
            "process": process or "unknown",
            "title": title or "unknown",
            "start": datetime.fromtimestamp(start_ts).isoformat(),
            "end": datetime.fromtimestamp(end_ts).isoformat(),
            "duration_seconds": round(duration, 1),
        }
        try:
            with open(self._today_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[HistoryLogger] Write error: {e}")

    def flush_current_segment(self):
        with self._lock:
            if self._current_process is not None and self._segment_start is not None:
                now = time.time()
                duration = now - self._segment_start
                if duration >= 1.0:
                    self._write_segment(
                        self._current_process, self._current_title,
                        self._segment_start, now, duration
                    )
                self._current_process = None
                self._segment_start = None

    def get_today_summary(self) -> dict:
        totals = {}
        path = self._today_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        proc = record.get("process", "unknown")
                        totals[proc] = totals.get(proc, 0) + record.get("duration_seconds", 0)
            except Exception as e:
                print(f"[HistoryLogger] Read error: {e}")

        # Include in-progress segment
        with self._lock:
            if self._current_process is not None and self._segment_start is not None:
                elapsed = time.time() - self._segment_start
                totals[self._current_process] = totals.get(self._current_process, 0) + elapsed

        return totals

    def get_time_for_app(self, spoken_name: str) -> float:
        resolved = resolve_app_alias(spoken_name)
        totals = self.get_today_summary()
        matched = 0.0
        for proc, seconds in totals.items():
            if resolved in proc.lower() or proc.lower() in resolved:
                matched += seconds
        return matched


# Singleton
history_logger = HistoryLogger()
