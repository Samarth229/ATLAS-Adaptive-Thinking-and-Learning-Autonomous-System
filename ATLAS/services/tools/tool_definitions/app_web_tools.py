import os
import subprocess
import webbrowser

from services.tools.tool_definitions.app_launcher_v0_1.launcher import open_app


def _open_youtube():
    webbrowser.open("https://youtube.com")
    return "Opening YouTube."


def _open_google(arg=None):
    if arg and arg.strip():
        webbrowser.open(f"https://google.com/search?q={arg.strip()}")
        return f"Searching Google for {arg.strip()}."
    webbrowser.open("https://google.com")
    return "Opening Google."


def _open_chrome():
    candidates = [
        os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Google\\Chrome\\Application\\chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Google\\Chrome\\Application\\chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google\\Chrome\\Application\\chrome.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            subprocess.Popen([path])
            return "Opening Chrome."
    return "Chrome not found. Please make sure it's installed."


def _open_brave():
    candidates = [
        os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
    ]
    for path in candidates:
        if os.path.exists(path):
            subprocess.Popen([path])
            return "Opening Brave."
    return "Brave not found. Please make sure it's installed."


def _open_default_browser():
    webbrowser.open("about:blank")
    return "Opening browser."


def _open_vscode():
    try:
        subprocess.Popen(["code"], shell=True)
        return "Opening VS Code."
    except Exception as e:
        return f"Could not open VS Code: {e}"


def _open_explorer():
    subprocess.Popen("explorer")
    return "Opening File Explorer."


def _open_notepad():
    subprocess.Popen("notepad.exe")
    return "Opening Notepad."


def _open_downloads():
    path = os.path.expanduser("~/Downloads")
    subprocess.Popen(f'explorer "{path}"', shell=True)
    return "Opening Downloads folder."


def register_all(matcher):
    # search google for X — needs_arg=True first so it takes priority
    matcher.register(["search google for", "search for", "google search for"], _open_google, needs_arg=True)
    matcher.register([
        "open youtube", "youtube", "go to youtube", "launch youtube",
        "play youtube", "open you tube",
    ], _open_youtube)
    matcher.register([
        "open google", "google", "go to google", "launch google",
        "open google.com",
    ], _open_google)
    matcher.register([
        "open brave", "launch brave", "start brave",
        "brave browser", "open brave browser",
    ], _open_brave)
    matcher.register([
        "open chrome", "launch chrome", "start chrome",
        "open google chrome", "chrome browser",
    ], _open_chrome)
    matcher.register([
        "open the browser", "open browser", "open a browser",
        "launch browser", "start browser",
    ], _open_default_browser)
    matcher.register([
        "open vs code", "open vscode", "open code", "launch vs code",
        "launch vscode", "start vs code", "open visual studio code",
        "open visual studio",
    ], _open_vscode)
    matcher.register([
        "open file explorer", "open explorer", "file explorer",
        "open files", "open my files", "show files",
    ], _open_explorer)
    matcher.register([
        "open notepad", "launch notepad", "start notepad",
        "open text editor", "open a text file",
    ], _open_notepad)
    matcher.register([
        "open downloads", "downloads folder", "open my downloads",
        "go to downloads", "show downloads",
    ], _open_downloads)
    # Bare fallback keywords for multi-command splitting ("open brave and vs code")
    matcher.register(["brave"], _open_brave)
    matcher.register(["chrome"], _open_chrome)
    matcher.register(["vs code", "vscode"], _open_vscode)
    # Generic launcher — MUST be last. Catches "open X" for any app not matched above.
    # Uses Start Menu search + drive fallback + caching.
    matcher.register(["open", "launch", "start"], open_app, needs_arg=True)
