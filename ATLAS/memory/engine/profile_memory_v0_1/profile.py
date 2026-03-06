import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
PROFILE_PATH = BASE_DIR / "memory" / "structured" / "user_profile.json"

class ProfileMemoryV0_1:

    def load(self):
        if not PROFILE_PATH.exists():
            return {}
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data):
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def update(self, key, value):
        profile = self.load()
        profile[key] = value
        self.save(profile)