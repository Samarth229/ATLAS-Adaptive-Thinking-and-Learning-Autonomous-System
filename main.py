import signal
import sys
import os

# Redirect stdout/stderr to log file when running without a console (pythonw.exe).
_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "collector_output.log")
if sys.stdout is None or not hasattr(sys.stdout, "write"):
    sys.stdout = open(_LOG_PATH, "a", buffering=1, encoding="utf-8")
    sys.stderr = sys.stdout

from collector import collector
from indicator import LiveIndicator


def main():
    collector.start()
    indicator = LiveIndicator(is_alive_callback=collector.is_alive)

    def handle_shutdown(sig, frame):
        print("[Main] Shutdown signal received.")
        indicator.stop()
        collector.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    print("[Main] DataCollector running. Green square should appear top-right.")
    indicator.start()  # blocks on tkinter mainloop


if __name__ == "__main__":
    main()
