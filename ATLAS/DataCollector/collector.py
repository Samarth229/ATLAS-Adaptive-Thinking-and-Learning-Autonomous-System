import os
import json
import time
import threading
from datetime import datetime

import psutil

try:
    import win32process
    import win32gui
except ImportError:
    win32process = None
    win32gui = None


_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "activity_history")
_POLL_INTERVAL = 2

_TRACKED_BACKGROUND_APPS = {
    "discord.exe", "whatsapp.root.exe", "telegram.exe",
    "spotify.exe", "steam.exe", "leagueclientux.exe", "leagueclient.exe",
    "valorant.exe", "epicgameslauncher.exe",
    "brave.exe", "chrome.exe", "msedge.exe", "firefox.exe",
    "code.exe", "pycharm64.exe", "studio64.exe",
    "obs64.exe", "vlc.exe",
    "outlook.exe", "winword.exe", "excel.exe", "powerpnt.exe",
    "slack.exe", "zoom.exe", "teams.exe",
}


class DataCollector:
    """
    Standalone activity tracker. Logs:
    1. Focus-change segments (one JSONL record per continuous focus period)
    2. Background-apps snapshots (only when the running-app set changes)
    """

    def __init__(self):
        os.makedirs(_DATA_DIR, exist_ok=True)
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._current_process = None
        self._current_title = None
        self._segment_start = None
        self._last_known_apps = set()
        self._is_alive = False

    def _today_focus_path(self):
        return os.path.join(_DATA_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_focus.jsonl")

    def _today_background_path(self):
        return os.path.join(_DATA_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_background.jsonl")

    def is_alive(self) -> bool:
        return self._is_alive

    def _get_active_window_info(self):
        title = None
        process_name = None
        try:
            if win32gui:
                hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(hwnd)
                if win32process and title:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        process_name = psutil.Process(pid).name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except Exception:
            pass
        return title or None, process_name

    def _get_running_apps(self):
        apps = set()
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"]
                if name and name.lower() in _TRACKED_BACKGROUND_APPS:
                    apps.add(name.lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return apps

    def get_last_snapshot_summary(self) -> str:
        if not self._last_known_apps:
            return "No tracked background apps currently detected."
        return "Currently running: " + ", ".join(sorted(self._last_known_apps))

    def _write_focus_segment(self, process, title, start_ts, end_ts, duration):
        record = {
            "process": process or "unknown",
            "title": title or "unknown",
            "start": datetime.fromtimestamp(start_ts).isoformat(),
            "end": datetime.fromtimestamp(end_ts).isoformat(),
            "duration_seconds": round(duration, 1),
        }
        try:
            with open(self._today_focus_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[DataCollector] Focus write error: {e}")

    def _write_background_snapshot(self, apps_set):
        record = {
            "timestamp": datetime.now().isoformat(),
            "running_apps": sorted(apps_set),
        }
        try:
            with open(self._today_background_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[DataCollector] Background write error: {e}")

    def _flush_current_segment(self):
        if self._current_process is not None and self._segment_start is not None:
            now = time.time()
            duration = now - self._segment_start
            if duration >= 1.0:
                self._write_focus_segment(
                    self._current_process, self._current_title,
                    self._segment_start, now, duration
                )

    def _poll_loop(self):
        last_title = None

        while self._running:
            try:
                self._is_alive = True
                title, process_name = self._get_active_window_info()

                if title != last_title:
                    now = time.time()
                    if self._current_process is not None and self._segment_start is not None:
                        duration = now - self._segment_start
                        if duration >= 1.0:
                            self._write_focus_segment(
                                self._current_process, self._current_title,
                                self._segment_start, now, duration
                            )
                    self._current_process = process_name
                    self._current_title = title
                    self._segment_start = now
                    last_title = title

                current_apps = self._get_running_apps()
                if current_apps != self._last_known_apps:
                    self._write_background_snapshot(current_apps)
                    self._last_known_apps = current_apps

            except Exception as e:
                print(f"[DataCollector] Poll error: {e}")
                self._is_alive = False

            time.sleep(_POLL_INTERVAL)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("[DataCollector] Started.")

    def stop(self):
        self._running = False
        self._flush_current_segment()
        self._is_alive = False
        print("[DataCollector] Stopped.")


collector = DataCollector()
