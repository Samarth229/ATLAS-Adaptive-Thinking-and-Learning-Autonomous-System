import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()

BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "system.log"
STATE_FILE = BASE_DIR / "memory" / "system_state.json"

REQUIRED_DIRECTORIES = [
    "memory/interactions",
    "memory/structured",
    "memory/reflections",
    "memory/milestones",
    "interface/voice",
    "interface/dashboard",
    "cognition/reasoning",
    "cognition/behavior",
    "cognition/adaptation",
    "services/daemon",
    "services/scheduler",
    "logs"
]

def load_json(path):
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content)
    except json.JSONDecodeError:
        write_log(f"Corrupted JSON detected at {path.name}. Resetting file.")
        return None

def write_log(message):
    LOG_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def validate_directories():
    for relative_path in REQUIRED_DIRECTORIES:
        path = BASE_DIR / relative_path
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            write_log(f"Directory auto-created: {relative_path}")

def load_previous_state():
    state = load_json(STATE_FILE)
    return state if state else None

def save_current_state(state_data):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=4)

def initialize_system():
    validate_directories()

    identity_path = BASE_DIR / "atlas_core" / "identity" / "identity.json"
    ethics_path = BASE_DIR / "atlas_core" / "ethics" / "core_principles.json"
    growth_path = BASE_DIR / "atlas_core" / "growth" / "growth_charter.json"
    version_path = BASE_DIR / "atlas_core" / "versioning" / "version.json"

    identity = load_json(identity_path)
    ethics = load_json(ethics_path)
    growth = load_json(growth_path)
    version = load_json(version_path)

    previous_state = load_previous_state()
    boot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    current_milestones = version.get("milestones", [])
    current_milestone_count = len(current_milestones)

    if previous_state is None:
        write_log("First system boot detected.")
        boot_count = 1
        last_milestone_count = current_milestone_count
    else:
        boot_count = previous_state.get("boot_count", 0) + 1

        if previous_state.get("last_version") != version["current_version"]:
            write_log(
                f"Version change detected: "
                f"{previous_state.get('last_version')} -> {version['current_version']}"
            )

        last_milestone_count = previous_state.get("last_milestone_count", 0)

        if current_milestone_count > last_milestone_count:
            new_milestones = current_milestones[last_milestone_count:]
            for milestone in new_milestones:
                write_log(f"New milestone recorded: {milestone}")

    boot_message = (
        f"{identity['system_name']} initialized | "
        f"Version {version['current_version']} | "
        f"Mode: {identity['operational_mode']} | "
        f"Boot #{boot_count}"
    )

    write_log(boot_message)

    save_current_state({
        "last_version": version["current_version"],
        "last_boot_time": boot_time,
        "boot_count": boot_count,
        "last_mode": identity["operational_mode"],
        "last_milestone_count": current_milestone_count
    })

    console.print(
        Panel.fit(
            f"[bold cyan]{identity['system_name']}[/bold cyan]\n"
            f"Version: {version['current_version']}\n"
            f"Mode: {identity['operational_mode']}\n"
            f"Boot Count: {boot_count}\n"
            f"Milestones: {current_milestone_count}\n"
            f"Created by: {identity['created_by']}",
            title="System Initialization",
            border_style="green"
        )
    )

    return {
        "identity": identity,
        "ethics": ethics,
        "growth": growth,
        "version": version
    }