import json
from pathlib import Path
from datetime import datetime


class GoalMemoryV0_1:
    def __init__(self):
        base_dir = Path(__file__).resolve().parents[3]
        self.goal_file = base_dir / "memory" / "structured" / "goals.json"

        if not self.goal_file.exists():
            self.goal_file.parent.mkdir(parents=True, exist_ok=True)
            self._save({
                "goals": [],
                "last_updated": None
            })

    def _load(self):
        with open(self.goal_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):
        with open(self.goal_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def add_goal(self, goal_text: str):
        data = self._load()

        goal_entry = {
            "goal": goal_text.strip(),
            "created_at": datetime.now().isoformat(),
            "progress_notes": []
        }

        data["goals"].append(goal_entry)
        data["last_updated"] = datetime.now().isoformat()

        self._save(data)

    def list_goals(self):
        data = self._load()
        return data.get("goals", [])

    def add_progress_note(self, goal_index: int, note: str):
        data = self._load()

        if 0 <= goal_index < len(data["goals"]):
            data["goals"][goal_index]["progress_notes"].append({
                "note": note,
                "timestamp": datetime.now().isoformat()
            })

            data["last_updated"] = datetime.now().isoformat()
            self._save(data)
            return True

        return False