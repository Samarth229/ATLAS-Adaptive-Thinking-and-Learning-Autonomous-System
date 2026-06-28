import json
import os
import requests
from datetime import datetime
from difflib import SequenceMatcher


_OLLAMA_URL = "http://localhost:11434/api/generate"
_EXTRACTION_MODEL = "mistral"
_LONG_TERM_MEMORY_PATH = r"E:\ATLAS\ATLAS\memory\structured\extracted_facts.json"

_EXTRACTION_PROMPT_TEMPLATE = """You are analyzing a conversation between a user and their personal AI assistant.

Extract ONLY genuinely durable facts about the USER that would be worth remembering long-term — things like:
- Where they live or are located
- Personal preferences (likes/dislikes about movies, food, hobbies, etc.)
- Relationships (family members, friends mentioned by name/relation)
- Ongoing projects or interests they mention
- Important dates or recurring commitments

DO NOT extract:
- One-off commands or requests ("open chrome", "remind me to call mom", "what's the time")
- Questions the user asked
- Anything ATLAS said, only facts ABOUT THE USER
- Trivial or one-time details with no lasting value

Conversation:
{conversation_text}

Respond ONLY with a JSON array of facts, each as {{"category": "...", "fact": "..."}}.
If there is nothing worth remembering, respond with an empty array: []
Do not include any text outside the JSON array.
"""


def _format_conversation(exchanges: list) -> str:
    lines = []
    for ex in exchanges:
        speaker = "User" if ex.get("speaker") == "user" else "ATLAS"
        lines.append(f"{speaker}: {ex.get('text', '')}")
    return "\n".join(lines)


def _load_existing_facts() -> list:
    if not os.path.exists(_LONG_TERM_MEMORY_PATH):
        return []
    try:
        with open(_LONG_TERM_MEMORY_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return []


def _save_facts(facts: list):
    try:
        os.makedirs(os.path.dirname(_LONG_TERM_MEMORY_PATH), exist_ok=True)
        with open(_LONG_TERM_MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(facts, f, indent=2)
    except Exception as e:
        print(f"[MemoryExtraction] Save error: {e}")


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _is_duplicate(new_fact: dict, existing_facts: list, threshold: float = 0.6) -> bool:
    new_text = new_fact.get("fact", "").lower().strip()
    for existing in existing_facts:
        existing_text = existing.get("fact", "").lower().strip()
        if new_text == existing_text or new_text in existing_text or existing_text in new_text:
            return True
        if _text_similarity(new_text, existing_text) >= threshold:
            return True
    return False


def extract_facts_from_exchanges(exchanges: list) -> dict:
    if not exchanges:
        return {"new_facts_count": 0, "facts": [], "error": None}

    conversation_text = _format_conversation(exchanges)
    prompt = _EXTRACTION_PROMPT_TEMPLATE.format(conversation_text=conversation_text)

    try:
        response = requests.post(
            _OLLAMA_URL,
            json={
                "model": _EXTRACTION_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        raw_text = result.get("response", "").strip()

        start_idx = raw_text.find("[")
        end_idx = raw_text.rfind("]") + 1
        if start_idx == -1 or end_idx == 0:
            return {"new_facts_count": 0, "facts": [], "error": "No JSON array found in model response"}

        json_str = raw_text[start_idx:end_idx]
        new_facts = json.loads(json_str)

        if not isinstance(new_facts, list):
            return {"new_facts_count": 0, "facts": [], "error": "Model response was not a list"}

        existing_facts = _load_existing_facts()
        added = []

        for fact in new_facts:
            if not isinstance(fact, dict) or "category" not in fact or "fact" not in fact:
                continue
            if _is_duplicate(fact, existing_facts):
                continue
            fact["extracted_at"] = datetime.now().isoformat()
            existing_facts.append(fact)
            added.append(fact)

        if added:
            _save_facts(existing_facts)

        return {"new_facts_count": len(added), "facts": added, "error": None}

    except requests.exceptions.ConnectionError:
        return {"new_facts_count": 0, "facts": [], "error": "Could not reach Ollama"}
    except json.JSONDecodeError as e:
        return {"new_facts_count": 0, "facts": [], "error": f"Could not parse model output as JSON: {e}"}
    except Exception as e:
        return {"new_facts_count": 0, "facts": [], "error": str(e)}


def get_all_facts() -> list:
    return _load_existing_facts()
