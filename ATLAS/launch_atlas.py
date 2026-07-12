import subprocess
import time
import os
import sys

_ATLAS_DIR = os.path.dirname(os.path.abspath(__file__))
_PYTHON_EXE = sys.executable
_MAIN_PY = os.path.join(_ATLAS_DIR, "main.py")
_ELECTRON_DIR = os.path.join(_ATLAS_DIR, "interface", "gui_electron")


def main():
    print("[Launcher] Starting ATLAS voice mode...")
    voice_process = subprocess.Popen(
        [_PYTHON_EXE, _MAIN_PY, "voice"],
        cwd=_ATLAS_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    print("[Launcher] Starting Flask backend server...")
    flask_process = subprocess.Popen(
        [_PYTHON_EXE, "-m", "interface.gui.flask_server"],
        cwd=_ATLAS_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    print("[Launcher] Waiting for Flask to be ready...")
    time.sleep(2)

    print("[Launcher] Starting Electron GUI...")
    electron_process = subprocess.Popen(
        ["npm", "start"],
        cwd=_ELECTRON_DIR,
        shell=True,
    )

    print("[Launcher] All processes started.")
    electron_process.wait()

    print("[Launcher] GUI closed. Shutting down voice mode and Flask server...")
    voice_process.terminate()
    flask_process.terminate()


if __name__ == "__main__":
    main()
