import time
import threading
import psutil

try:
    import win32process
    import win32gui
except ImportError:
    win32process = None
    win32gui = None

from services.monitoring.system_awareness_v0_1.history_logger import history_logger


_KNOWN_APPS = {
    "chrome.exe": "Chrome",
    "brave.exe": "Brave",
    "firefox.exe": "Firefox",
    "msedge.exe": "Edge",
    "code.exe": "VS Code",
    "explorer.exe": "File Explorer",
    "notepad.exe": "Notepad",
    "discord.exe": "Discord",
    "spotify.exe": "Spotify",
    "steam.exe": "Steam",
    "leagueclient.exe": "League of Legends",
    "valorant.exe": "Valorant",
    "whatsapp.exe": "WhatsApp",
    "telegram.exe": "Telegram",
    "obs64.exe": "OBS Studio",
    "photoshop.exe": "Photoshop",
    "winword.exe": "Word",
    "excel.exe": "Excel",
    "powerpnt.exe": "PowerPoint",
    "outlook.exe": "Outlook",
    "vlc.exe": "VLC",
    "epicgameslauncher.exe": "Epic Games Launcher",
    "ollama.exe": "Ollama",
    "ollama app.exe": "Ollama",
    "python.exe": "Python",
    "windowsterminal.exe": "Windows Terminal",
    "cmd.exe": "Command Prompt",
    "powershell.exe": "PowerShell",
}

_EXCLUDE_PATTERNS = [
    "svchost", "service", "helper", "agent", "daemon", "host",
    "notification", "update", "sync", "background", "tray",
    "rundll", "dllhost", "wmiprvse", "conhost", "audiodg",
    "smartdisplay", "armourycrate", "applemobiledevice",
    "fontdrvhost", "csrss", "lsass", "wininit", "winlogon",
    "spoolsv", "dwm", "ctfmon", "searchindexer", "registry",
    "memory compression", "system", "secure system",
    "acpower", "appactions", "aggregator", "asus", "acer", "hp",
    "dell", "lenovo", "realtek", "nvidia", "amd", "intel",
]


class SystemAwareness:
    """
    Passive background system state tracker.
    Polls active window + resource usage every POLL_INTERVAL seconds.
    Exposes a thread-safe snapshot via get_state().
    """

    POLL_INTERVAL = 2

    def __init__(self):
        self._KNOWN_APPS_LOWER = {k.lower(): v for k, v in _KNOWN_APPS.items()}
        self._lock = threading.Lock()
        self._state = {
            "active_window_title": None,
            "active_process_name": None,
            "window_focus_start": None,
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "battery_percent": None,
            "battery_plugged": None,
        }
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("[SystemAwareness] Background monitoring started.")

    def stop(self):
        self._running = False
        history_logger.flush_current_segment()

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

    def _poll_loop(self):
        last_title = None
        focus_start = time.time()

        while self._running:
            try:
                title, process_name = self._get_active_window_info()
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent

                battery_percent = None
                battery_plugged = None
                battery = psutil.sensors_battery()
                if battery:
                    battery_percent = battery.percent
                    battery_plugged = battery.power_plugged

                if title != last_title:
                    focus_start = time.time()
                    last_title = title
                    history_logger.on_window_change(process_name, title)

                with self._lock:
                    self._state.update({
                        "active_window_title": title,
                        "active_process_name": process_name,
                        "window_focus_start": focus_start,
                        "cpu_percent": cpu,
                        "ram_percent": ram,
                        "battery_percent": battery_percent,
                        "battery_plugged": battery_plugged,
                    })
            except Exception as e:
                print(f"[SystemAwareness] Poll error: {e}")

            time.sleep(self.POLL_INTERVAL)

    def get_state(self) -> dict:
        with self._lock:
            return dict(self._state)

    def get_focus_duration_seconds(self) -> float:
        with self._lock:
            start = self._state.get("window_focus_start")
        if start is None:
            return 0.0
        return time.time() - start

    def get_running_apps(self, limit=8) -> list:
        """Returns a friendly, deduplicated list of recognizable user-facing apps."""
        found_known = []
        found_other = []
        seen = set()

        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"]
                if not name:
                    continue
                name_lower = name.lower()

                if name_lower in seen:
                    continue
                seen.add(name_lower)

                # Known app — use friendly name
                if name_lower in self._KNOWN_APPS_LOWER:
                    friendly = self._KNOWN_APPS_LOWER[name_lower]
                    if friendly not in found_known:
                        found_known.append(friendly)
                    continue

                # Skip background/system processes
                if any(pattern in name_lower for pattern in _EXCLUDE_PATTERNS):
                    continue

                # Other recognizable app — strip .exe
                clean_name = name[:-4] if name_lower.endswith(".exe") else name
                if len(clean_name) > 2 and clean_name not in found_other:
                    found_other.append(clean_name)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        result = found_known[:limit]
        remaining = limit - len(result)
        if remaining > 0:
            result.extend(found_other[:remaining])
        return result


# Singleton — shared across the app
system_awareness = SystemAwareness()
