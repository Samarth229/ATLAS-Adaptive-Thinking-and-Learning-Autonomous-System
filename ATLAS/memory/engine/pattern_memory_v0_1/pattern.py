import json
from pathlib import Path
from collections import Counter
from datetime import datetime


class PatternMemoryV0_1:
    def __init__(self):
        base_dir = Path(__file__).resolve().parents[3]
        self.pattern_file = base_dir / "memory" / "structured" / "patterns.json"

        if not self.pattern_file.exists():
            self.pattern_file.parent.mkdir(parents=True, exist_ok=True)
            self._save({"keywords": {}, "last_updated": None})

    def _load(self):
        with open(self.pattern_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):
        with open(self.pattern_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def log_text(self, text: str):
        words = [
            word.lower()
            for word in text.split()
            if len(word) > 4
        ]

        data = self._load()
        counter = Counter(data.get("keywords", {}))

        counter.update(words)

        data["keywords"] = dict(counter)
        data["last_updated"] = datetime.now().isoformat()

        self._save(data)

    def analyze_recent(self, top_n=5):
        data = self._load()
        keywords = data.get("keywords", {})

        if not keywords:
            return None

        counter = Counter(keywords)
        return counter.most_common(top_n)