import subprocess
import os

_ATLAS_ROOT = r"E:\ATLAS"
_ATLAS_CODE = r"E:\ATLAS\ATLAS"


def _open_atlas_project():
    try:
        subprocess.Popen(["code", _ATLAS_CODE], shell=True)
        return "Opening the ATLAS project in VS Code."
    except Exception as e:
        return f"Could not open project: {e}"


def _git_status():
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=_ATLAS_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout.strip()
        if not output:
            return "Git status: working tree is clean. No changes."

        lines = output.splitlines()
        modified = sum(1 for l in lines if l.startswith(" M") or l.startswith("M "))
        added = sum(1 for l in lines if l.startswith("A ") or l.startswith("??"))
        deleted = sum(1 for l in lines if l.startswith(" D") or l.startswith("D "))
        total = len(lines)

        parts = []
        if modified:
            parts.append(f"{modified} modified")
        if added:
            parts.append(f"{added} new or untracked")
        if deleted:
            parts.append(f"{deleted} deleted")
        if not parts:
            parts.append(f"{total} changed")

        return f"Git status: {', '.join(parts)} file{'s' if total != 1 else ''}."
    except subprocess.TimeoutExpired:
        return "Git status timed out."
    except Exception as e:
        return f"Could not run git status: {e}"


def register_all(matcher):
    matcher.register([
        "open atlas project", "open atlas", "open the atlas project",
        "open the project", "open my project", "launch atlas",
        "go to atlas", "start atlas project", "atlas project",
        # STT mis-transcription variants for "open atlas"
        "openatlas", "open at last", "open at last project",
        "open atlas.", "atlas",
    ], _open_atlas_project)
    matcher.register([
        "git status", "git state", "what's changed in git",
        "what changed", "any changes", "check git", "repo status",
        "what files changed",
    ], _git_status)
