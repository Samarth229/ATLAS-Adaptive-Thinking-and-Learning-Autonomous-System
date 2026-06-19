import os
import re
import json
import glob
import difflib
import subprocess

try:
    import win32com.client
except ImportError:
    win32com = None

_CACHE_PATH = r"E:\Requirements\app_launcher_cache.json"
_LOCAL = os.environ.get("LOCALAPPDATA", "")
_APPDATA = os.environ.get("APPDATA", "")


def _find_versioned_exe(base_dir: str, pattern: str):
    candidates = glob.glob(os.path.join(base_dir, pattern))
    return sorted(candidates)[-1] if candidates else None


# Tier 1 — exact known paths, resolved once at import time.
# Always returns confidence 1.0 — no fuzzy matching involved.
_RIOT_CLIENT = r"C:\Riot Games\Riot Client\RiotClientServices.exe"

# Riot games can't be launched by direct exe — Vanguard anti-cheat blocks it.
# Must go through RiotClientServices with --launch-product and --launch-patchline.
_RIOT_GAMES = {
    "league_of_legends": ["league of legends", "league", "lol"],
    "valorant":          ["valorant", "val"],
}

_KNOWN_APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "brave": os.path.join(_LOCAL, r"BraveSoftware\Brave-Browser\Application\brave.exe"),
    "vs code": os.path.join(_LOCAL, r"Programs\Microsoft VS Code\Code.exe"),
    "vscode": os.path.join(_LOCAL, r"Programs\Microsoft VS Code\Code.exe"),
    "visual studio code": os.path.join(_LOCAL, r"Programs\Microsoft VS Code\Code.exe"),
    "discord": _find_versioned_exe(os.path.join(_LOCAL, "Discord"), r"app-*\Discord.exe"),
    "slack": _find_versioned_exe(os.path.join(_LOCAL, "slack"), r"app-*\slack.exe"),
    "spotify": os.path.join(_APPDATA, r"Spotify\Spotify.exe"),
    "notepad": r"C:\Windows\System32\notepad.exe",
    "calculator": r"C:\Windows\System32\calc.exe",
    "paint": r"C:\Windows\System32\mspaint.exe",
    "task manager": r"C:\Windows\System32\Taskmgr.exe",
}

_START_MENU_DIRS = [
    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
]

_SKIP_DIRS = {
    "windows kits", "microsoft sdks", "microsoft visual studio",
    "dotnet", "windowsapps",
}

_BAD_EXES = {
    "update.exe", "uninstall.exe", "setup.exe", "installer.exe",
    "unins000.exe", "crashreporter.exe", "helper.exe", "updater.exe",
    "unitycrashhandler64.exe", "unitycrashhandler32.exe", "crashhandler.exe",
}


def _is_bad_exe(path: str) -> bool:
    return os.path.basename(path).lower() in _BAD_EXES


def _get_steam_library_paths() -> list[str]:
    vdf_path = r"C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf"
    paths = []
    if not os.path.exists(vdf_path):
        return paths
    try:
        with open(vdf_path, "r", encoding="utf-8") as f:
            content = f.read()
        for m in re.findall(r'"path"\s+"([^"]+)"', content):
            lib_path = m.replace("\\\\", "\\")
            common = os.path.join(lib_path, "steamapps", "common")
            if os.path.exists(common):
                paths.append(common)
    except Exception:
        pass
    return paths


def _get_fallback_search_roots() -> list[str]:
    roots = [
        os.path.join(_LOCAL, "Programs"),
        r"C:\Riot Games",
    ]
    roots.extend(_get_steam_library_paths())
    return [r for r in roots if os.path.exists(r)]


def _similarity(query: str, target: str) -> float:
    """
    Word-aware similarity that prevents character-level false positives.

    Key behaviours:
    - "planet crafter" does NOT match "cisco packet tracer" (no shared words)
    - "marvel rivals" DOES match "MarvelRivals_Launcher" (CamelCase split
      gives words "marvel rivals launcher" → all query words found → 0.95)
    - Short target "Marvel" matching long query "marvel rivals" is penalised
      proportionally (0.90 × coverage ≈ 0.41) so it falls below threshold
    """
    def _norm(s):
        # Split CamelCase before lowering ("MarvelRivals" → "Marvel Rivals")
        s = re.sub(r'([a-z])([A-Z])', r'\1 \2', s)
        return s.lower().replace("-", " ").replace(".", " ").replace("_", " ").strip()

    q = _norm(query)
    t = _norm(target)

    if q == t:
        return 1.0
    # Query is a substring of target ("marvel rivals" in "marvel rivals launcher")
    if q in t:
        return 0.95
    # Target is a substring of query — penalise proportionally so a short
    # target ("marvel") matching a long query ("marvel rivals") scores low.
    if t in q:
        return 0.90 * (len(t) / max(len(q), 1))

    q_words = set(w for w in q.split() if len(w) > 2)
    t_words = set(w for w in t.split() if len(w) > 2)

    if q_words and t_words:
        if q_words.issubset(t_words):
            return 0.90
        overlap = len(q_words & t_words) / len(q_words | t_words)
        if overlap > 0:
            char_ratio = difflib.SequenceMatcher(None, q, t).ratio()
            return max(overlap * 0.85, char_ratio)

    return difflib.SequenceMatcher(None, q, t).ratio()


def _load_cache() -> dict:
    if os.path.exists(_CACHE_PATH):
        try:
            with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict):
    try:
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[AppLauncher] Cache write error: {e}")


def _resolve_known_app(name: str):
    path = _KNOWN_APPS.get(name)
    return path if path and os.path.exists(path) else None


def _resolve_lnk_target(lnk_path: str):
    if win32com is None:
        return None
    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(lnk_path)
        target = shortcut.Targetpath
        if target and os.path.exists(target):
            return target
    except Exception:
        pass
    return None


def _search_start_menu_with_confidence(name: str):
    all_shortcuts = []
    for start_dir in _START_MENU_DIRS:
        if os.path.exists(start_dir):
            all_shortcuts.extend(glob.glob(os.path.join(start_dir, "**", "*.lnk"), recursive=True))

    if not all_shortcuts:
        return None

    best_score = 0.0
    best_shortcut = None
    for lnk_path in all_shortcuts:
        shortcut_name = os.path.splitext(os.path.basename(lnk_path))[0]
        score = _similarity(name, shortcut_name)
        if score > best_score:
            best_score = score
            best_shortcut = (shortcut_name.lower(), lnk_path)

    if best_shortcut and best_score >= 0.55:
        shortcut_name, lnk_path = best_shortcut
        resolved = _resolve_lnk_target(lnk_path)
        target = resolved if resolved else lnk_path
        if not _is_bad_exe(target):
            return (target, best_score, shortcut_name)

    return None


def _search_drives_fallback_with_confidence(name: str):
    candidates = []
    for root in _get_fallback_search_roots():
        try:
            for dirpath, subdirs, filenames in os.walk(root):
                if any(s in dirpath.lower() for s in _SKIP_DIRS):
                    subdirs.clear()
                    continue
                for fname in filenames:
                    if not fname.lower().endswith(".exe"):
                        continue
                    full_path = os.path.join(dirpath, fname)
                    if _is_bad_exe(full_path):
                        continue
                    # Keep spaces in exe name — "Planet Crafter.exe" → "Planet Crafter"
                    fname_clean = os.path.splitext(fname)[0]
                    score = _similarity(name, fname_clean)
                    if score >= 0.70:
                        candidates.append((score, fname_clean, full_path))
        except Exception:
            continue

    if candidates:
        # Primary: highest score. Tie-break: longest matched name (more specific),
        # then shallowest path depth (launcher at game root beats nested binary).
        candidates.sort(key=lambda x: (-x[0], -len(x[1]), x[2].count(os.sep)))
        score, matched_name, path = candidates[0]
        return (path, score, matched_name)
    return None


def _search_uwp_apps(name: str):
    """Tier 4: Microsoft Store / UWP apps — resolves the real AppId from the package manifest."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-AppxPackage | Select-Object Name, PackageFamilyName | ConvertTo-Json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None

        apps = json.loads(result.stdout)
        if isinstance(apps, dict):
            apps = [apps]

        # Build two maps: one for scoring (lowercase), one to recover original Name
        lower_to_original = {}
        lower_to_family = {}
        for app in apps:
            if app.get("Name") and app.get("PackageFamilyName"):
                lower_to_original[app["Name"].lower()] = app["Name"]
                lower_to_family[app["Name"].lower()] = app["PackageFamilyName"]

        best_score = 0.0
        best_lower = None
        for app_lower in lower_to_original:
            score = _similarity(name, app_lower)
            if score > best_score:
                best_score = score
                best_lower = app_lower

        if not best_lower or best_score < 0.55:
            return None

        original_name = lower_to_original[best_lower]
        family = lower_to_family[best_lower]

        # Look up the actual Application ID from the package manifest
        manifest_result = subprocess.run(
            ["powershell", "-Command",
             f"(Get-AppxPackage -Name '{original_name}' | Get-AppxPackageManifest)"
             ".Package.Applications.Application.Id"],
            capture_output=True, text=True, timeout=15
        )
        app_id = manifest_result.stdout.strip()
        if not app_id:
            app_id = "App"  # fallback if manifest lookup fails
        # Multi-app packages return multiple IDs — use the first
        if "\n" in app_id:
            app_id = app_id.split("\n")[0].strip()

        uri = f"shell:appsFolder\\{family}!{app_id}"
        return (uri, best_score, best_lower)
    except Exception as e:
        print(f"[AppLauncher] UWP search error: {e}")
    return None


def resolve_app_path_with_confidence(name: str):
    """
    Returns (path, confidence, matched_name) or None.
    confidence 1.0 = exact/known match, <0.75 = uncertain (ask user to confirm).
    """
    name_clean = name.lower().strip().rstrip("?!.,").strip()
    cache = _load_cache()

    if name_clean in cache and os.path.exists(cache[name_clean]):
        print(f"[DEBUG] '{name}' -> CACHE hit: {cache[name_clean]}")
        return (cache[name_clean], 1.0, name_clean)

    path = _resolve_known_app(name_clean)
    if path:
        print(f"[DEBUG] '{name}' -> TIER 1 (known): {path}")
        return (path, 1.0, name_clean)

    result = _search_start_menu_with_confidence(name_clean)
    if result:
        path, confidence, matched_name = result
        print(f"[DEBUG] '{name}' -> TIER 2 (start menu): conf={confidence:.3f} matched='{matched_name}' path={path}")
        if confidence >= 0.75:
            cache[name_clean] = path
            _save_cache(cache)
        return (path, confidence, matched_name)

    result = _search_drives_fallback_with_confidence(name_clean)
    if result:
        path, confidence, matched_name = result
        print(f"[DEBUG] '{name}' -> TIER 3 (drive search): conf={confidence:.3f} matched='{matched_name}' path={path}")
        if confidence >= 0.85:
            cache[name_clean] = path
            _save_cache(cache)
        return (path, confidence, matched_name)

    result = _search_uwp_apps(name_clean)
    if result:
        path, confidence, matched_name = result
        print(f"[DEBUG] '{name}' -> TIER 4 (UWP): conf={confidence:.3f} matched='{matched_name}' path={path}")
        return (path, confidence, matched_name)

    print(f"[DEBUG] '{name}' -> NOT FOUND in any tier")
    return None


def resolve_app_path(name: str):
    result = resolve_app_path_with_confidence(name)
    return result[0] if result else None


def _launch_riot_game(product_id: str) -> str:
    """Launch a Riot game via RiotClientServices (required — Vanguard blocks direct exe)."""
    if not os.path.exists(_RIOT_CLIENT):
        return "Riot Client not found. Make sure Riot Games is installed."
    try:
        subprocess.Popen(
            [_RIOT_CLIENT, f"--launch-product={product_id}", "--launch-patchline=live"],
        )
        return f"Opening {product_id.replace('_', ' ').title()}."
    except Exception as e:
        return f"Couldn't launch via Riot Client: {e}"


def open_app(arg=None) -> str:
    if not arg or not arg.strip():
        return "Which app would you like me to open?"

    app_name = arg.strip().rstrip("?!.,").strip()
    app_lower = app_name.lower()

    # Riot games must go through RiotClientServices — Vanguard anti-cheat
    # blocks any process that isn't the Riot Client from spawning the game exe.
    for product_id, aliases in _RIOT_GAMES.items():
        if app_lower in aliases:
            return _launch_riot_game(product_id)

    result = resolve_app_path_with_confidence(app_name)

    if result is None:
        return f"I couldn't find an app called {app_name}. Make sure it's installed."

    path, confidence, matched_name = result

    if confidence < 0.75:
        return (f"I'm not certain, but the closest match I found was '{matched_name}'. "
                f"Try saying the full name to be more specific.")

    try:
        if path.startswith("shell:"):
            # UWP/shell: URIs must go through cmd's START — explorer.exe
            # would browse the folder instead of launching the app.
            subprocess.Popen(["cmd", "/c", "start", "", path], shell=False)
        else:
            os.startfile(path)
        return f"Opening {app_name}."
    except Exception as e:
        return f"Found {app_name} but couldn't launch it: {e}"
